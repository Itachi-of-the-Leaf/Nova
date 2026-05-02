export interface ReferenceEntry {
  number: number;
  text: string;
}

export interface AppState {
  step: number;
  rawText: string;
  metadata: {
    title: string;
    authors: string;
    abstract: string;
    headings: string;
    references: string;
    references_list?: ReferenceEntry[];
    confidence?: number;
    [key: string]: any;
  };
  lexicalHashOriginal?: string;
  lexicalHashFinal?: string;
  semanticHashOriginal?: string;
  semanticHashFinal?: string;
  semanticHashScore?: number;
  fileName?: string;
}