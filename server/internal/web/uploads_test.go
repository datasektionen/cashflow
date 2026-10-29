package web

import "testing"

func TestSafeName(t *testing.T) {
	for in, want := range map[string]string{
		"Kvitto från ICA.HEIC":         "Kvitto-fran-ICA.jpg",
		`C:\Users\me\receipt (1).jpeg`: "receipt--1.jpg",
		"../../etc/passwd":             "passwd.jpg",
		"???":                          "fil.jpg",
		"ett väldigt långt filnamn som aldrig tar slut och fortsätter och fortsätter.jpg": "ett-valdigt-langt-filnamn-som-aldrig-tar-slut-och-fortsa.jpg",
	} {
		if got := safeName(in, ".jpg"); got != want {
			t.Errorf("safeName(%q) = %q, want %q", in, got, want)
		}
		if len(safeName(in, ".jpg")) > 60 {
			t.Errorf("safeName(%q) is too long", in)
		}
	}
	if id := newUploadID(); len("c4/"+id+"/")+60 > 100 {
		t.Errorf("storage keys can exceed core_file.file's 100 characters: id %q", id)
	}
}
