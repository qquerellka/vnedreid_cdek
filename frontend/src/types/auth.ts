export interface UserRegisterRequest {
  email: string;
  password: string;
}
 
export interface AuthResponse {
  access_token: string;
  message: string;
} 