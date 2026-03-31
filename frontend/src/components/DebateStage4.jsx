import ReactMarkdown from 'react-markdown';
import './DebateStage4.css';

function verdictColor(verdict) {
  if (verdict === 'PRO') return '#2e7d32';
  if (verdict === 'AGAINST') return '#c62828';
  return '#f57c00';
}

function verdictLabel(verdict) {
  if (verdict === 'PRO') return '✅ Pro wins';
  if (verdict === 'AGAINST') return '❌ Against wins';
  if (verdict === 'TIE') return '🤝 Tie';
  return '❓ Unknown';
}

export default function DebateStage4({ stage4 }) {
  if (!stage4) return null;

  const color = verdictColor(stage4.verdict);

  return (
    <div className="debate-stage debate-stage4">
      <h3 className="debate-stage-title">⚖️ Stage 4: Judge's Verdict</h3>

      <div className="judge-header">
        <div className="judge-label">
          Judge: {stage4.model.split('/')[1] || stage4.model}
        </div>
        <div className="verdict-badge" style={{ background: color }}>
          {verdictLabel(stage4.verdict)}
        </div>
        {stage4.confidence > 0 && (
          <div className="confidence-bar-wrapper">
            <span className="confidence-label">Confidence: {stage4.confidence}%</span>
            <div className="confidence-bar">
              <div
                className="confidence-fill"
                style={{ width: `${stage4.confidence}%`, background: color }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="judge-evaluation markdown-content">
        <ReactMarkdown>{stage4.evaluation}</ReactMarkdown>
      </div>
    </div>
  );
}
