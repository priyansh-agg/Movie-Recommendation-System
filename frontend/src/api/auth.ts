import client from './client';

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
}

export async function register(
  email: string,
  username: string,
  password: string,
): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>('/auth/register', {
    email,
    username,
    password,
  });
  return data;
}

export async function login(
  email: string,
  password: string,
): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>('/auth/login', {
    email,
    password,
  });
  return data;
}

export async function refreshAccessToken(
  refreshToken: string,
): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return data;
}
