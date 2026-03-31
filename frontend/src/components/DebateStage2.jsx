import ReactMarkdown from 'react-markdown';
import './DebateStage2.css';

export default function DebateStage2({ stage2 }) {
  if (!stage2) return null;

  return (
    <div className="debate-stage debate-stage2">
      <h3 className="debate-stage-title">🔄 Stage 2: Rebuttal Round</h3>
      <div className="debate-columns">
        <div className="debate-side pro-side">
          <div className="debate-side-header pro-header">
            ✅ Pro Agent – Rebuttal
            <span className="debate-model-tag">{stage2.pro.model.split('/')[1] || stage2.pro.model}</span>
          </div>
          <div className="debate-side-content markdown-content">
            <ReactMarkdown>{stage2.pro.rebuttal}</ReactMarkdown>
          </div>
        </div>

        <div className="debate-side against-side">
          <div className="debate-side-header against-header">
            ❌ Against Agent – Rebuttal
            <span className="debate-model-tag">{stage2.against.model.split('/')[1] || stage2.against.model}</span>
          </div>
          <div className="debate-side-content markdown-content">
            <ReactMarkdown>{stage2.against.rebuttal}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
