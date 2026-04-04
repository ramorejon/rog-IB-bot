# Inside Bar Discord Bot

Receives TradingView webhook alerts per ticker and aggregates them into a daily table posted to Discord.

## Endpoints

### Webhook (TradingView)
POST /webhook

Example payload:
{
  "ticker": "AAPL",
  "inside_count": "2"
}

### Send to Discord
GET /send

## Deployment (Render)

1. Create Web Service
2. Connect repo
3. Set environment variable:
   DISCORD_WEBHOOK = your webhook URL

## TradingView Setup

Webhook URL:
https://your-app.onrender.com/webhook

Message:
{
  "ticker": "{{ticker}}",
  "inside_count": "{{plot_0}}"
}

## Scheduling

Use cron-job.org to call:
/send

At ~4:05 PM ET daily