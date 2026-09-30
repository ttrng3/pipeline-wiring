# Intent (accepted)

Status: accepted by Ty 30/09 ("fix heartbeat notes", then "approve", in chat).

Found by the #7 review: `data/status.json`, which Pages serves, copied the first 160 characters of each repo's heartbeat note, and the page showed it as hover text. Those notes carried source file names (one with a person's name), part of a Drive folder id and a trade fill count. That breaks this repo's rule: status only, never a person's details or a pipeline's own data.
