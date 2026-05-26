# Outreach pitch flow (Blueprint v3 aligned)

## Who gets what

| Lead type | Hunt mode | Service | What you sell |
|-----------|-----------|---------|----------------|
| **No website** | `m10_no_website` | **Website** | Modern site + lead capture (Method 10) |
| **Outdated site** | `m02_outdated` | **Website** | Rebuild / mobile / SSL (Method 02) |
| **Professional site** | any (audit: score ≥6, mobile, SSL) | **Automation** | AI chat, lead capture, online booking (Method 24) |
| **Real estate** | any | **Automation** | AI lead intake + follow-up |

Blueprint §9: **+3** no site or pre-2018 site → website pitch. **-2** professional site + SEO → automation pitch, not a new site.

## Email flow (each lead)

1. **Audit** their URL (M02) if they have a website  
2. **Resolve** `service_to_pitch` = `website` or `automation`  
3. **Icebreaker** — observation + gap only (no pitch)  
4. **Email 1** — offer matches service + demo link + CTA  
5. **Emails 2–4** — follow-ups stay on same service angle  

Logs show: `service=automation tier=modern — AI chatbot + lead automation...`

## Instantly variables

| Variable | Meaning |
|----------|---------|
| `{{icebreaker}}` | Opening 1–2 sentences |
| `{{demo_url}}` | Live preview |
| `{{service_to_pitch}}` | `website` or `automation` |
| `{{body_1}}` | Full email 1 |

## Run

```bash
# Outdated → website pitch
python scripts/run_campaign.py --niche plumber --city "Dallas TX" --leads 2 --hunt-mode m02_outdated --instantly

# No website → website pitch
python scripts/run_campaign.py --niche plumber --city "Dallas TX" --leads 2 --hunt-mode m10_no_website --instantly
```

Professional sites contacted via other hunts get **automation** copy automatically after audit.
