package claims

import (
	"fmt"
	"strings"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

// Email is an outbox entry: spam renders Content as Markdown.
type Email struct {
	To      string `json:"to"`
	Subject string `json:"subject"`
	Content string `json:"content"`
}

// commentEmail is Cashflow 3's email.html, linking to the claim.
func commentEmail(publicURL string, kind Kind, number int64, description string, owner db.GetCommentRecipientRow, author, body string) Email {
	noun, path := "Utlägget", "expenses"
	subject := author + " har lagt till en kommentar på ditt utlägg."
	if kind == Invoice {
		noun, path = "Fakturan", "invoices"
		subject = author + " har lagt till en kommentar på din faktura."
	}
	link := fmt.Sprintf("%s/%s/%d", strings.TrimSuffix(publicURL, "/"), path, number)
	content := fmt.Sprintf("# Hej, %s!\n\n%s \"[%s](%s)\" har fått en ny kommentar av %s:\n\n%s\n",
		owner.Name, noun, description, link, author, body)
	return Email{To: owner.Email, Subject: subject, Content: content}
}
