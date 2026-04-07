import { useState } from 'react';
import AppShell from '../components/layout/AppShell';
import { handoffSections } from '../data/mock';
import { ChevronDown, ChevronRight, FileSignature } from 'lucide-react';

export default function HandoffPage() {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({ 0: true, 1: true, 2: true, 3: true });
  const [notes, setNotes] = useState('');
  const [sections] = useState(handoffSections);

  const toggleSection = (i: number) => {
    setExpanded((prev) => ({ ...prev, [i]: !prev[i] }));
  };

  const renderPreview = () => {
    return sections.map((section, i) => {
      if (section.editable) {
        return notes ? (
          <div key={i} className="mb-4">
            <h4 className="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-1">{section.title}</h4>
            <p className="text-sm text-neutral-600">{notes}</p>
          </div>
        ) : null;
      }
      return (
        <div key={i} className="mb-4">
          <h4 className="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-1">{section.title}</h4>
          {section.content && <p className="text-sm text-neutral-600 leading-relaxed">{section.content}</p>}
          {section.items && (
            <ul className="list-disc list-inside text-sm text-neutral-600 space-y-1">
              {section.items.map((item, j) => (
                <li key={j}>{item}</li>
              ))}
            </ul>
          )}
        </div>
      );
    });
  };

  return (
    <AppShell>
      <h1 className="text-lg font-semibold text-neutral-900 mb-4">End of shift handoff</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Editable content */}
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-2">
            Handoff content (auto-generated)
          </h2>

          {sections.map((section, i) => (
            <div key={i} className="bg-white border border-neutral-200 rounded-lg">
              <button
                onClick={() => toggleSection(i)}
                className="w-full flex items-center justify-between px-4 py-3 text-left"
              >
                <span className="text-sm font-medium text-neutral-700">{section.title}</span>
                {expanded[i] ? <ChevronDown className="w-4 h-4 text-neutral-400" /> : <ChevronRight className="w-4 h-4 text-neutral-400" />}
              </button>
              {expanded[i] && (
                <div className="px-4 pb-4 border-t border-neutral-100 pt-3">
                  {section.editable ? (
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add personal observations for the next coordinator..."
                      className="w-full h-24 text-sm text-neutral-600 border border-neutral-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/30"
                    />
                  ) : (
                    <>
                      {section.content && (
                        <p className="text-sm text-neutral-600 leading-relaxed">{section.content}</p>
                      )}
                      {section.items && (
                        <ul className="space-y-2">
                          {section.items.map((item, j) => (
                            <li key={j} className="flex items-start gap-2">
                              <input type="checkbox" defaultChecked={false} className="mt-0.5 rounded border-neutral-300 text-primary focus:ring-primary/20" />
                              <span className="text-sm text-neutral-600">{item}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Right: Preview */}
        <div>
          <h2 className="text-sm font-semibold text-neutral-800 uppercase tracking-wide mb-2">Preview</h2>
          <div className="bg-white border border-neutral-200 rounded-lg p-6">
            <div className="border-b border-neutral-100 pb-3 mb-4">
              <h3 className="text-sm font-semibold text-neutral-800">Shift Handoff Report</h3>
              <div className="text-xs text-neutral-400 mt-1">
                Morning shift · April 6, 2026 · Maya R. → Afternoon coordinator
              </div>
            </div>
            {renderPreview()}
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="flex items-center justify-between mt-6 bg-white border border-neutral-200 rounded-lg px-4 py-3">
        <div className="flex items-center gap-2 text-xs text-neutral-400">
          <FileSignature className="w-4 h-4" />
          Handoff will be signed with your e-signature and timestamped
        </div>
        <div className="flex items-center gap-3">
          <button className="text-sm text-neutral-500 hover:text-primary">Save as draft</button>
          <button className="bg-primary text-white text-sm font-medium py-2 px-5 rounded-lg hover:bg-primary/90 transition-colors">
            Save and sign
          </button>
        </div>
      </div>
    </AppShell>
  );
}
