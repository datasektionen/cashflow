package main

import (
	"bytes"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"strings"
	"time"

	"golang.org/x/image/font"
	"golang.org/x/image/font/basicfont"
	"golang.org/x/image/math/fixed"
)

// receiptPNG draws a till receipt, so the receipt viewer has photos to show.
func receiptPNG(title string, amountOre int64, date time.Time) ([]byte, error) {
	const width, height, scale = 200, 260, 3
	small := image.NewRGBA(image.Rect(0, 0, width, height))
	draw.Draw(small, small.Bounds(), &image.Uniform{color.RGBA{250, 248, 240, 255}}, image.Point{}, draw.Src)

	lines := []string{
		"   KONGLIG BUTIK AB", "   Org.nr 802411-8948", "", date.Format("2006-01-02 15:04"), "",
	}
	lines = append(lines, wrap(asciiOnly(title), 26)...)
	lines = append(lines, "", strings.Repeat("-", 28), fmt.Sprintf("TOTAL SEK %17s", kronor(amountOre)),
		fmt.Sprintf("varav moms %15s", kronor(amountOre/5)), strings.Repeat("-", 28), "", "   Tack for besoket!")

	d := &font.Drawer{Dst: small, Src: image.NewUniform(color.RGBA{40, 40, 40, 255}), Face: basicfont.Face7x13}
	for i, line := range lines {
		d.Dot = fixed.P(6, 18+i*14)
		d.DrawString(line)
	}

	// Scale up with nearest neighbour for a crisp, phone-photo-sized image.
	big := image.NewRGBA(image.Rect(0, 0, width*scale, height*scale))
	for y := range height * scale {
		for x := range width * scale {
			big.Set(x, y, small.At(x/scale, y/scale))
		}
	}
	var buf bytes.Buffer
	err := png.Encode(&buf, big)
	return buf.Bytes(), err
}

// receiptPDF writes a one-page invoice PDF by hand; the format needs only a
// few objects and exact byte offsets.
func receiptPDF(title, recipient string, amountOre int64, date time.Time) []byte {
	text := []string{
		"FAKTURA", "", asciiOnly(title), "", "Till: " + asciiOnly(recipient) + ", Konglig Datasektionen",
		"Fakturadatum: " + date.Format(time.DateOnly), "Forfallodatum: " + date.AddDate(0, 0, 30).Format(time.DateOnly),
		"", "Att betala: " + kronor(amountOre) + " SEK", "Bankgiro: 123-4567",
	}
	var content strings.Builder
	content.WriteString("BT /F1 22 Tf 72 760 Td (FAKTURA) Tj /F1 12 Tf\n")
	for _, line := range text[1:] {
		fmt.Fprintf(&content, "0 -20 Td (%s) Tj\n", strings.NewReplacer(`(`, `\(`, `)`, `\)`).Replace(line))
	}
	content.WriteString("ET")

	objects := []string{
		"<< /Type /Catalog /Pages 2 0 R >>",
		"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
		"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
		fmt.Sprintf("<< /Length %d >>\nstream\n%s\nendstream", content.Len(), content.String()),
	}
	var pdf bytes.Buffer
	pdf.WriteString("%PDF-1.4\n")
	offsets := make([]int, len(objects))
	for i, obj := range objects {
		offsets[i] = pdf.Len()
		fmt.Fprintf(&pdf, "%d 0 obj\n%s\nendobj\n", i+1, obj)
	}
	xref := pdf.Len()
	fmt.Fprintf(&pdf, "xref\n0 %d\n0000000000 65535 f \n", len(objects)+1)
	for _, off := range offsets {
		fmt.Fprintf(&pdf, "%010d 00000 n \n", off)
	}
	fmt.Fprintf(&pdf, "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n", len(objects)+1, xref)
	return pdf.Bytes()
}

func kronor(ore int64) string {
	return fmt.Sprintf("%d,%02d", ore/100, ore%100)
}

// asciiOnly folds Swedish letters for the built-in fonts, which lack them.
func asciiOnly(s string) string {
	return strings.NewReplacer("å", "a", "ä", "a", "ö", "o", "Å", "A", "Ä", "A", "Ö", "O").Replace(s)
}

func wrap(s string, width int) []string {
	var lines []string
	line := ""
	for _, word := range strings.Fields(s) {
		if len(line)+len(word)+1 > width && line != "" {
			lines = append(lines, line)
			line = ""
		}
		if line != "" {
			line += " "
		}
		line += word
	}
	return append(lines, line)
}
