# Casino bot

Install: `pip install -r requirements.txt`   |   Run: `python main.py`
config.py me apna BOT_TOKEN rakhna (zip wali config me placeholder hai).
Purani `games.py` delete kar do (ab `games/` folder hai).

## Files
- main.py, utils.py, ui.py, tg.py, database.py, admin.py, fair.py, config.py
- cardimg.py (/start card) | refcard.py (/refer card) | stmtcard.py (/statement card) | qr.py (QR)
- payments.py (/transactions) | referral.py (/refer) | statement.py (/statement)
- reports.py + pdfgen.py (sab PDFs)
- games/ : dice.py, tower.py, mines.py, common.py, registry.py

## User commands (private ones group me chalayein to DM me aate hain)
/bal  /start  /play  /dice /tower /mines
/statement            -> card + pages + Export PDF
/transactions (/payhistory)      /transactionspdf (/paypdf)
/refer   /referpdf

## Admin (/admin)
Users & PDFs: user ID/@username daalo -> Games PDF, Refer PDF, Payments PDF, Statement PDF,
Record Deposit / Withdrawal, Add/Deduct balance.
Settings pages: Branding, Start Card, Bets, Games, Deposit/Withdraw links, Referral System, Statement & History.

## Gateway se jodna (deposit/withdraw data)
    import payments
    payments.add_payment(user_id, "deposit", 25.0, asset="USDT_POLYGON", tx="0x...")
    payments.add_payment(user_id, "withdrawal", 10.0, asset="USDT_POLYGON", tx="0x...", status="Paid")
Withdraw check ke liye: `database.wager_left(user_id)` > 0 ho to withdrawal rok do (referral claim ka wager requirement).

---
## Group control, owner lock, /profile (v2)

**Approved groups only** — bot sirf un groups me chalta hai jo admin ne allow kiye ho (DM hamesha chalta hai).
- Admin bot ko group me add kare -> group apne aap allow.
- Ya group me admin `/allow` bheje. Band karne ke liye `/disallow`.
- Admin panel -> **👥 Allowed Groups** me list dikhti hai aur wahin se remove kar sakte ho.
- Purane groups jahan bot pehle se tha, wahan ek baar admin `/allow` bheje.

**Owner lock** — group me jo user `/play`, `/mines`, `/profile` ... bheje, bot ka wo message aur uske saare buttons
sirf usi ke hain. Dusra user dabaye to alert aata hai; usse apna command bhejna hota hai. (grouplock.py)

**/admin** group me bheji jaye to panel DM me khulta hai (group me nahi).

**Game commands** — `/mines`, `/mines 5`, `/mines 5 10`, `/tower 2 hard`, `/dice 5 crazy` ab game seedha start nahi karte;
setup screen kholte hain (bet/mines pehle se set). Game 'Start Game' dabane par hi shuru hota hai.

**/profile** — photo card (level, wager rank, win rate, balance...) + **🎨 Change Theme** (8 themes).
Design: profilecard.py (THEMES me naya theme jodo). Levels: profilecard.LEVELS (15 levels, wager se).

### v3 changes
- `/profile` ab **Rich Message** hai: photo card + buttons ek hi message ke andar (UI mode `inline`; `classic` me buttons neeche,
  `plain` me purana photo+caption card). Theme badalne par card usi message me update hota hai.
- Card se **Net Profit hata diya** (ab sirf Balance aur Total Won).
- **Group me `/start`** -> us user ka profile card + `/bal` ek saath. **DM me `/start`** pehle jaisa (home card).

### v4 changes
- `/bal` ab Rich Message (Deposit/Withdraw buttons message ke andar).
- Group me `/start` -> sirf `/bal` jaisa balance message. DM me `/start` pehle jaisa.
- `/profile`: card ke saath koi text nahi; buttons: Change Theme / Deposit + Withdraw / Statement + Payments / Refer & Earn.
- Dice ka final result Rich Message; "won" ab total payout dikhata hai (bet + profit). Mines/Tower pehle se "Bet -> payout" dikhate hain.
- ui._rich_body: multi-line text aur <blockquote> rich HTML me sahi paragraphs me banta hai.
