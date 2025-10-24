# Cost Optimization & Monitoring

Track and control your OpenAI API costs with real-time monitoring and daily caps.

---

## Overview

The cost monitoring system helps you:
- Track API spending in real-time
- Set daily spending caps to prevent overages
- View 30-day cost history
- Break down costs by category
- Monitor token usage per activity

**Average Cost:** ~$0.15/month with smart detection (75% savings from baseline)

---

## Key Features

### 1. Daily Cost Caps

Set a maximum daily spend to prevent unexpected charges.

**Default:** $2.00/day
**Notification Threshold:** $1.50/day

```json
// Configure in database via API
{
  "daily_cap": 2.00,
  "notification_threshold": 1.50
}
```

When the cap is reached, the camera manager will skip OpenAI analysis until the next day (midnight UTC).

### 2. Real-Time Tracking

Every API call is tracked with:
- **Input tokens:** Tokens sent to OpenAI
- **Output tokens:** Tokens received from OpenAI
- **Total cost:** Calculated based on GPT-4o-mini pricing
- **Timestamp:** When the call was made
- **Category:** Activity category for breakdown

### 3. Cost History

View spending trends over the last 30 days:
- Daily totals
- Token usage
- Request counts
- Cost trends

---

## API Endpoints

### Get Today's Cost

```bash
GET /api/cost/today
```

**Response:**
```json
{
  "daily_spent": 0.1250,
  "daily_cap": 2.00,
  "total_tokens": 8500,
  "requests_today": 45,
  "percentage_used": 6.3,
  "threshold_reached": false,
  "cap_reached": false,
  "by_category": [
    {"category": "Productivity", "cost": 0.0500, "tokens": 3200},
    {"category": "Health", "cost": 0.0300, "tokens": 2100}
  ]
}
```

### Update Cost Settings

```bash
PUT /api/cost/settings
Content-Type: application/json

{
  "daily_cap": 3.00,
  "notification_threshold": 2.00
}
```

### Get Cost History

```bash
GET /api/cost/history
```

**Response:**
```json
{
  "history": [
    {
      "date": "2025-10-23",
      "total_cost": 0.1250,
      "total_tokens": 8500,
      "total_requests": 45
    },
    {
      "date": "2025-10-22",
      "total_cost": 0.1420,
      "total_tokens": 9200,
      "total_requests": 48
    }
  ]
}
```

---

## Cost Breakdown

### GPT-4o-mini Pricing

- **Input:** $0.150 per 1M tokens
- **Output:** $0.600 per 1M tokens

### Average Per Capture

Without YOLOv8:
- ~1,500 input tokens (image + prompt)
- ~150 output tokens (analysis)
- **Cost:** ~$0.00023 per capture
- **Monthly (96 captures/day):** ~$0.66/month

With YOLOv8 (75% savings):
- Only ~24 captures/day analyzed (change detection)
- **Cost:** ~$0.00023 per capture
- **Monthly:** ~$0.15/month

---

## Cost Optimization Tips

### 1. Enable Smart Detection

Ensure YOLOv8 person detection is enabled in `config.json`:

```json
{
  "activity_detection": {
    "enabled": true,
    "force_analyze_interval_minutes": 30
  }
}
```

This reduces OpenAI calls by 50-80%.

### 2. Increase Capture Interval

Change from 15 minutes to 30 minutes:

```json
{
  "cameras": [
    {
      "capture_interval_minutes": 30
    }
  ]
}
```

This halves your API usage.

### 3. Reduce Active Hours

Only capture during hours you're home:

```json
{
  "cameras": [
    {
      "active_hours": {
        "start": "08:00",
        "end": "22:00"
      }
    }
  ]
}
```

### 4. Monitor Daily Spending

Check your spending regularly:

```bash
curl http://localhost:8000/api/cost/today \
  --cookie "session=YOUR_SESSION"
```

---

## Database Storage

All cost data is stored in the `activities` table:

```sql
SELECT
  DATE(timestamp) as date,
  SUM(cost) as daily_cost,
  SUM(tokens_used) as daily_tokens,
  COUNT(*) as daily_requests
FROM activities
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

Cost settings are in the `cost_settings` table:

```sql
SELECT * FROM cost_settings WHERE id = 1;
```

---

## React Integration

### Display Today's Cost

```javascript
import { useState, useEffect } from 'react';

function CostMonitor() {
  const [costData, setCostData] = useState(null);

  useEffect(() => {
    async function fetchCost() {
      const response = await fetch('http://localhost:8000/api/cost/today', {
        credentials: 'include'
      });
      const data = await response.json();
      setCostData(data);
    }

    fetchCost();
    const interval = setInterval(fetchCost, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  if (!costData) return <div>Loading...</div>;

  return (
    <div className="cost-monitor">
      <h3>Today's API Cost</h3>
      <div className="cost-display">
        ${costData.daily_spent.toFixed(4)} / ${costData.daily_cap.toFixed(2)}
      </div>
      <div className="cost-bar">
        <div
          className="cost-bar-fill"
          style={{ width: `${costData.percentage_used}%` }}
        />
      </div>
      <div className="cost-stats">
        <span>{costData.total_tokens.toLocaleString()} tokens</span>
        <span>{costData.requests_today} requests</span>
      </div>
    </div>
  );
}
```

---

## Troubleshooting

### High Costs

**Problem:** Spending more than expected

**Solutions:**
1. Check if YOLOv8 is enabled: `activity_detection.enabled: true`
2. Review capture interval: increase from 15 to 30 minutes
3. Reduce active hours to only when home
4. Check `GET /api/cost/today` for breakdown by category
5. Review `force_analyze_interval_minutes` setting

### Cost Cap Not Working

**Problem:** System continues analyzing after cap reached

**Solutions:**
1. Check `cost_settings` table exists and has data
2. Verify camera_manager is reading from database
3. Restart camera_manager service
4. Check logs for cost cap warnings

### Token Count Seems Wrong

**Problem:** Token usage doesn't match expectations

**Solutions:**
1. OpenAI token counting can vary slightly
2. Images always use ~1,500 input tokens for GPT-4o-mini
3. Longer/more detailed responses use more output tokens
4. Check actual API responses in logs

---

## See Also

- [Activity Detection](ACTIVITY_DETECTION.md) - YOLOv8 cost optimization
- [API Reference](../API_REFERENCE.md) - Complete API documentation
- [Quick Reference](../QUICK_REFERENCE.md) - Common commands
