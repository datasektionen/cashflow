// Package storage reads claim attachments from S3, where Cashflow 3's
// django-storages put them under the "media/" prefix.
package storage

import (
	"context"
	"errors"
	"fmt"
	"io"
	"mime"
	"path"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
)

// prefix matches Cashflow 3's STORAGES["default"]["OPTIONS"]["location"].
const prefix = "media/"

var ErrNotFound = errors.New("file not found")

type Config struct {
	Bucket          string
	Region          string
	AccessKeyID     string
	SecretAccessKey string
	// Endpoint is set for S3-compatible servers in development; it implies
	// path-style addressing.
	Endpoint string
}

type Store struct {
	client *s3.Client
	bucket string
}

func New(ctx context.Context, cfg Config) (*Store, error) {
	awsCfg, err := config.LoadDefaultConfig(ctx,
		config.WithRegion(cfg.Region),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(cfg.AccessKeyID, cfg.SecretAccessKey, "")),
	)
	if err != nil {
		return nil, fmt.Errorf("storage: %w", err)
	}
	client := s3.NewFromConfig(awsCfg, func(o *s3.Options) {
		if cfg.Endpoint != "" {
			o.BaseEndpoint = aws.String(cfg.Endpoint)
			o.UsePathStyle = true
		}
	})
	return &Store{client: client, bucket: cfg.Bucket}, nil
}

// Object is an open file; the caller closes Body.
type Object struct {
	Body          io.ReadCloser
	ContentType   string
	ContentLength int64
}

// Open fetches the file stored as name (core_file.file).
func (s *Store) Open(ctx context.Context, name string) (Object, error) {
	out, err := s.client.GetObject(ctx, &s3.GetObjectInput{Bucket: aws.String(s.bucket), Key: aws.String(prefix + name)})
	if err != nil {
		if _, ok := errors.AsType[*types.NoSuchKey](err); ok {
			return Object{}, ErrNotFound
		}
		return Object{}, fmt.Errorf("storage: get %s: %w", name, err)
	}
	return Object{Body: out.Body, ContentType: ContentType(name), ContentLength: aws.ToInt64(out.ContentLength)}, nil
}

// Put stores a file; used by the seed command (and uploads, later).
func (s *Store) Put(ctx context.Context, name string, body io.Reader) error {
	_, err := s.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(s.bucket), Key: aws.String(prefix + name), Body: body, ContentType: aws.String(ContentType(name)),
	})
	return err
}

// ContentType guesses from the extension, as stored objects from Cashflow 3
// carry no reliable type. Unknown types download instead of rendering.
func ContentType(name string) string {
	if t := mime.TypeByExtension(strings.ToLower(path.Ext(name))); t != "" {
		return t
	}
	return "application/octet-stream"
}

// Exists reports whether a file is stored as name.
func (s *Store) Exists(ctx context.Context, name string) (bool, error) {
	_, err := s.client.HeadObject(ctx, &s3.HeadObjectInput{Bucket: aws.String(s.bucket), Key: aws.String(prefix + name)})
	if _, ok := errors.AsType[*types.NotFound](err); ok {
		return false, nil
	}
	if err != nil {
		return false, fmt.Errorf("storage: head %s: %w", name, err)
	}
	return true, nil
}
