# October reporting policy

This is a project-authored trading review of UCI Online Retail data. The period is 1 October 2011 00:00 inclusive to 1 November 2011 00:00 exclusive, using the supplied timestamps. Amounts are signed Quantity × UnitPrice in GBP. The extract also contains adjacent-day transactions.

Ordinary sales have positive quantity and price and no C-prefixed invoice. Credits have negative quantity, positive price and a C-prefixed invoice, ignoring letter case. Other combinations, nonpositive prices, or missing essential business fields are exceptions. Essential fields are InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice and Country. Retain calculable exception amounts separately. Missing CustomerID is an attribution issue rather than a reason to exclude an otherwise valid sale or credit.

Each source_row_id identifies one physical occurrence. Equal business fields do not establish duplicate transmission. Each invoice identifier is a separate document; the supplied data provides no authorized credit-to-original-invoice linkage. The result is recorded transaction value, not audited revenue or cash received.

Keep source business facts available for review. A classified register may link to the supplied original fields through source_row_id. Out-of-period occurrences may remain in the original extract with a clear scope statement. Invoice and country analysis should distinguish sales, credits and exceptions. Correct static results and equivalent layouts are acceptable.
