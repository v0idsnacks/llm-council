import ReactMarkdown from 'react-markdown';
import './DebateStage3.css';

export default function DebateStage3({ stage3 }) {
  if (!stage3) return null;

  return (
    <div className="debate-stage debate-stage3">
      <h3 className="debate-stage-title">🏁 Stage 3: Final Statements</h3>
      <div className="debate-columns">
        <div className="debate-side pro-side">
          <div className="debate-side-header pro-header">
            ✅ Pro Agent – Closing
            <span className="debate-model-tag">{stage3.pro.model.split('/')[1] || stage3.pro.model}</span>
          </div>
          <div className="debate-side-content markdown-content">
            <ReactMarkdown>{stage3.pro.final_statement}</ReactMarkdown>
          </div>
        </div>

        <div className="debate-side against-side">
          <div className="debate-side-header against-header">
            ❌ Against Agent – Closing
            <span className="debate-model-tag">{stage3.against.model.split('/')[1] || stage3.against.model}</span>
          </div>
          <div className="debate-side-content markdown-content">
            <ReactMarkdown>{stage3.against.final_statement}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
