import React from "react";
import { BookOpen, Cpu, FlaskConical, Lightbulb, Zap } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface TutorOutputPanelProps {
  data: {
    queryType: string;
    concepts: string[];
    formulas: Array<{
      formula: string;
      name: string;
      topic: string;
      meaning: string;
    }>;
    explanation: string;
    ragContent: Array<{
      title: string;
      content: string;
    }>;
  } | null;
  className?: string;
}

export function TutorOutputPanel({ data, className = "" }: TutorOutputPanelProps) {
  if (!data) {
    return (
      <div className={`glass-strong rounded-3xl p-12 flex flex-col items-center justify-center text-center gap-6 ${className}`}>
        <div className="w-20 h-20 rounded-3xl bg-white/5 flex items-center justify-center animate-pulse">
          <BookOpen className="w-10 h-10 text-muted-foreground/30" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-muted-foreground/50">Analysis Results</h3>
          <p className="text-sm text-muted-foreground/30 mt-2">Enter a question on the left to see concepts, formulas, and explanations.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar ${className}`}>
      {/* Query Type Badge */}
      <div className="flex justify-end">
        <div className="px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
          <span>Query Type:</span>
          <span className={
            data.queryType === 'formula' ? 'text-[var(--neon-cyan)]' : 
            data.queryType === 'concept' ? 'text-[var(--neon-purple)]' : 
            'text-[var(--neon-yellow)]'
          }>
            {data.queryType}
          </span>
        </div>
      </div>

      {/* Section 1: Related Concepts */}
      <section className="glass-strong rounded-3xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <Lightbulb className="w-5 h-5 text-[var(--neon-yellow)]" />
          <h3 className="text-lg font-bold">Related Concepts</h3>
        </div>
        <div className="flex flex-wrap gap-3">
          {data.concepts.length > 0 ? (
            data.concepts.map((concept, i) => (
              <div
                key={i}
                className="px-4 py-2 rounded-2xl bg-[var(--neon-purple)]/10 border border-[var(--neon-purple)]/30 text-[var(--neon-purple)] text-sm font-semibold animate-in fade-in zoom-in duration-300 shadow-[0_0_15px_rgba(192,38,211,0.1)]"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                {concept}
              </div>
            ))
          ) : (
            <div className="w-full p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
              <p className="text-sm text-muted-foreground italic">No specific concepts identified for this query.</p>
            </div>
          )}
        </div>
      </section>

      {/* Section 2: Relevant Formulas */}
      <section className="glass-strong rounded-3xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <Cpu className="w-5 h-5 text-[var(--neon-cyan)]" />
          <h3 className="text-lg font-bold">Relevant Formulas</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.formulas.length > 0 ? (
            data.formulas.map((f, i) => (
              <div
                key={i}
                className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-[var(--neon-cyan)]/50 transition-all group animate-in slide-in-from-bottom-4 duration-500"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <div className="text-2xl font-mono font-bold text-[var(--neon-cyan)] mb-2 group-hover:scale-105 transition-transform origin-left">
                  {f.formula}
                </div>
                <div className="text-sm font-bold text-foreground mb-1">{f.name}</div>
                <div className="text-xs text-muted-foreground italic mb-3">{f.topic}</div>
                <div className="text-xs text-muted-foreground leading-relaxed bg-black/20 p-2 rounded-lg">
                  {f.meaning}
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full p-4 rounded-2xl bg-white/5 border border-white/5 text-center">
              <p className="text-sm text-muted-foreground italic">No formulas directly relevant to this query were found.</p>
            </div>
          )}
        </div>
      </section>

      {/* Section 3: AI Explanation */}
      <section className="glass-strong rounded-3xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--neon-purple)]/10 blur-3xl -z-10" />
        <div className="flex items-center gap-3 mb-6">
          <Zap className="w-5 h-5 text-[var(--neon-purple)]" />
          <h3 className="text-lg font-bold">AI Explanation</h3>
        </div>
        <div className="text-foreground/90 leading-relaxed space-y-4 prose prose-invert max-w-none prose-headings:text-[var(--neon-purple)] prose-a:text-[var(--neon-cyan)]">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm, remarkMath]} 
            rehypePlugins={[rehypeKatex]}
            components={{
              h1: ({node, ...props}) => <h1 className="text-2xl font-bold mt-6 mb-4 text-white" {...props}/>,
              h2: ({node, ...props}) => <h2 className="text-xl font-bold mt-5 mb-3 text-[var(--neon-cyan)] border-b border-white/10 pb-2" {...props}/>,
              h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-4 mb-2 text-white" {...props}/>,
              p: ({node, ...props}) => <p className="mb-4 text-white/80" {...props}/>,
              ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-2 text-white/80" {...props}/>,
              ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-white/80" {...props}/>,
              li: ({node, ...props}) => <li className="" {...props}/>,
              strong: ({node, ...props}) => <strong className="font-bold text-white" {...props}/>,
            }}
          >
            {data.explanation}
          </ReactMarkdown>
        </div>
      </section>

      {/* Section 4: Textbook / RAG Content */}
      <section className="glass-strong rounded-3xl p-6 border-l-4 border-l-[var(--neon-blue)]">
        <div className="flex items-center gap-3 mb-6">
          <FlaskConical className="w-5 h-5 text-[var(--neon-blue)]" />
          <h3 className="text-lg font-bold">Textbook Content (RAG)</h3>
        </div>
        <div className="space-y-4">
          {data.ragContent.length > 0 ? (
            data.ragContent.map((item, i) => (
              <div 
                key={i} 
                className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/[0.08] transition-all animate-in fade-in slide-in-from-right-4 duration-500"
                style={{ animationDelay: `${i * 200}ms` }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 rounded-full bg-[var(--neon-blue)] shadow-[0_0_8px_var(--neon-blue)]" />
                  <h4 className="text-xs font-bold text-[var(--neon-blue)] uppercase tracking-wider">
                    {item.title}
                  </h4>
                </div>
                <p className="text-sm text-muted-foreground/90 leading-relaxed italic border-l-2 border-white/10 pl-4">
                  "{item.content}"
                </p>
              </div>
            ))
          ) : (
            <div className="p-8 rounded-2xl bg-white/5 border border-white/5 text-center">
              <p className="text-sm text-muted-foreground italic">No textbook excerpts found for this topic. I'll rely on general AI knowledge.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
