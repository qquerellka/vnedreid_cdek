export interface MonitoringRequest {
  position: string;
  salary: number;
  region: string;
  experience: string;
}

export interface Vacancy {
  id: string;
  request_id: string;
  name: string;
  url: string;
  salary_from: number | null;
  salary_to: number | null;
  experience: string;
  company_name: string;
  region: string;
  published_at: string;
}

export interface MonitoringResponse {
  vacancies_found: number;
  vacancies: Vacancy[];
} 