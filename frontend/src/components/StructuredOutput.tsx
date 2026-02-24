import React from 'react';

const REQUIRED_HEADINGS = [
  'Key insights',
  'Drivers and impacts',
  'Assumptions made',
  'Risks and uncertainties',
  'Suggested follow up questions',
];

function parseSections(text: string): Record<string, string> {
  const sections: Record<string, string> = {};
  const lines = text.split('\n');
  let current = '';

  const normalize = (value: string) =>
    value
      .trim()
      .replace(/^\*+|\*+$/g, '')
      .replace(/:$/, '')
      .replace(/\s+/g, ' ')
      .replace(/follow-up/i, 'follow up')
      .toLowerCase();

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const normalizedLine = normalize(line);
    const heading =
      REQUIRED_HEADINGS.find((h) => normalize(h) === normalizedLine) ||
      (normalize('Sources used') === normalizedLine ? 'Sources used' : null);
    if (heading) {
      current = heading;
      if (!sections[current]) sections[current] = '';
      continue;
    }
    if (current) {
      sections[current] = `${sections[current]}${rawLine}\n`;
    }
  }

  return sections;
}

interface StructuredOutputProps {
  responseText: string;
}

export default function StructuredOutput({ responseText }: StructuredOutputProps) {
  const sections = parseSections(responseText);

  return (
    <div className="output-sections">
      {REQUIRED_HEADINGS.map((heading) => (
        <section key={heading} className="output-card">
          <h3>{heading}</h3>
          <pre>{sections[heading]?.trim() || 'No content returned.'}</pre>
        </section>
      ))}
      <section className="output-card">
        <h3>Sources used</h3>
        <pre>{sections['Sources used']?.trim() || 'No sources listed.'}</pre>
      </section>
    </div>
  );
}
