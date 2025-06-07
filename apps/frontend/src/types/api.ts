export interface ScanResponse {
  job_id: string;
}

export interface StatusResponse {
  job_id: string;
  status: string;
}

export interface AIAnalyzeStatusResponse {
  job_id: string;
  ai_analyze_status: string;
}

export interface PlagiarismStatusResponse {
  job_id: string;
  plagiarism_check_status: string;
}

export interface PlagiarismResult {
  status: number;
  scanInformation: {
    service: string;
    scanTime: string;
    inputType: string;
  };
  result: {
    score: number;
    sourceCounts: number;
    textWordCounts: number;
    totalPlagiarismWords: number;
    identicalWordCounts: number;
    similarWordCounts: number;
  };
  sources: any[];
  similarWords: any[];
  indexes: any[];
  citations: any[];
  attackDetected: {
    zero_width_space: boolean;
    homoglyph_attack: boolean;
  };
  text: string;
  credits_used: number;
  credits_remaining: number;
}

export interface Article {
  title: string;
  year: number | null;
  link: string | null;
  citations: number | null;
  doi: string | null;
  verified: boolean;
  open_access: boolean;
  ai_analyzer_label?: 'real' | 'fake';
  ai_analyzer_score?: number;
  plagiarism_checker_results?: PlagiarismResult | null;
}

export interface JobData {
  job_id: string;
  author: string;
  results: Article[];
}

export interface JobDataResponse {
  job_id: string;
  job_data: JobData;
}

export type ProcessStage = 'idle' | 'scraping' | 'resolving' | 'extracting' | 'analyzing' | 'completed' | 'error';