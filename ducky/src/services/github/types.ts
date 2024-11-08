export interface PRDetails {
  number: number;
  title: string;
  description: string;
  author: string;
  baseBranch: string;
  mergeSha: string | null;
  fileCount: number;
  additions: number;
  deletions: number;
  files: {
    filename: string;
    status: string;
    additions: number;
    deletions: number;
    patch: string;
  }[];
}
