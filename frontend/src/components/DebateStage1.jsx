import ReactMarkdown from 'react-markdown';
import './DebateStage1.css';

export default function DebateStage1({ stage1 }) {
  if (!stage1) return null;

  return (
    <div className="debate-stage debate-stage1">
      <h3 className="debate-stage-title">🎤 Stage 1: Opening Arguments</h3>
      <div className="debate-columns">
        <div className="debate-side pro-side">
          <div className="debate-side-header pro-header">
            ✅ Pro Agent
            <span className="debate-model-tag">{stage1.pro.model.split('/')[1] || stage1.pro.model}</span>
          </div>
          <div className="debate-side-content markdown-content">
            <ReactMarkdown>{stage1.pro.argument}</ReactMarkdown>
          </div>
        </div>

        <div className="debate-side against-side">
          <div className="debate-side-header against-header">
            ❌ Against Agent
            <span className="debate-model-tag">{stage1.against.model.split('/')[1] || stage1.against.model}</span>
          </div>
          <div className="debate-side-content markdown-content">
            <ReactMarkdown>{stage1.against.argument}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}
