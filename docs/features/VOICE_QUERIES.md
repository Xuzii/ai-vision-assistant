# Voice Query System

Ask natural language questions about your activities using the voice query API.

---

## Overview

The voice query system lets you:
- Ask questions in plain English about your activities
- Get intelligent answers based on your activity history
- Track query history
- Optionally use voice input via Whisper API

**Example Questions:**
- "What was I doing at 2pm today?"
- "How much time did I spend being productive this week?"
- "Show my bedroom activities from yesterday"

---

## Features

### Natural Language Processing

Powered by GPT-4o-mini, the system understands:
- Time references (today, yesterday, last week, at 2pm)
- Activity categories (productive, exercise, cooking)
- Location references (kitchen, bedroom, office)
- Duration queries (how long, how much time)

### Context-Aware Answers

The system provides context from:
- Last 50 activities
- Today's category summaries
- Recent activity patterns
- Room-specific data

### Query History

All queries are saved with:
- Query text
- Response text
- Timestamp
- Tokens used
- Cost
- Execution time

---

## API Endpoints

### Text Query

```bash
POST /api/voice/query
Content-Type: application/json

{
  "query": "What was I doing at 2pm today?"
}
```

**Response:**
```json
{
  "success": true,
  "answer": "At 2:00 PM today, you were in the home office working on your laptop. This was categorized as a Productivity activity.",
  "tokens_used": 1250,
  "cost": 0.000375,
  "execution_time_ms": 850
}
```

### Voice Transcription (Optional)

```bash
POST /api/voice/transcribe
Content-Type: multipart/form-data

audio: <audio_file.wav>
```

**Response:**
```json
{
  "success": true,
  "text": "What was I doing at 2pm today?"
}
```

### Query History

```bash
GET /api/voice/history?limit=20
```

**Response:**
```json
{
  "queries": [
    {
      "id": 1,
      "query_text": "What was I doing at 2pm today?",
      "response_text": "At 2:00 PM today...",
      "timestamp": "2025-10-23T14:30:00",
      "tokens_used": 1250,
      "cost": 0.000375
    }
  ]
}
```

---

## React Integration

```javascript
import { useState } from 'react';

function VoiceQuery() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/voice/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ query })
      });

      const data = await response.json();
      if (data.success) {
        setAnswer(data.answer);
      }
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="voice-query">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your activities..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>

      {answer && (
        <div className="answer">
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Example Queries

### Time-Based

- "What was I doing at 9am today?"
- "What did I do yesterday afternoon?"
- "Show my activities from last Monday"

### Category-Based

- "How much time did I spend being productive today?"
- "When did I exercise this week?"
- "How long did I spend in the kitchen today?"

### Location-Based

- "What happened in the bedroom last night?"
- "Show all office activities from this week"
- "Where was I at 3pm yesterday?"

### Pattern Analysis

- "What do I usually do in the morning?"
- "How often do I exercise per week?"
- "What's my most common activity?"

---

## Cost Information

Voice queries use GPT-4o-mini for natural language processing:

- **Input:** ~2,000 tokens (context + query)
- **Output:** ~150 tokens (answer)
- **Cost per query:** ~$0.0004

**Monthly cost for occasional use:** <$0.50

Voice transcription (Whisper API):
- **Cost:** $0.006 per minute of audio
- **Typical query:** 5 seconds = ~$0.0005

---

## See Also

- [API Reference](../API_REFERENCE.md) - Complete API documentation
- [Cost Monitoring](COST_MONITORING.md) - Track your API costs
