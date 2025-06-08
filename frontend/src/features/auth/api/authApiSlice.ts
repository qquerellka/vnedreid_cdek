import { apiSlice } from '../../api/apiSlice';
import type { UserRegisterRequest, AuthResponse } from '../../../types/auth';

export const authApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    register: builder.mutation<AuthResponse, UserRegisterRequest>({
      query: (credentials) => ({
        url: '/register',
        method: 'POST',
        body: credentials,
      }),
      transformResponse: (response: AuthResponse) => {
        // The backend sets the cookie automatically, we just need to return the response
        return response;
      },
    }),
    login: builder.mutation<AuthResponse, UserRegisterRequest>({
      query: (credentials) => ({
        url: '/login',
        method: 'POST',
        body: credentials,
      }),
      transformResponse: (response: AuthResponse) => {
        // The backend sets the cookie automatically, we just need to return the response
        return response;
      },
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/logout',
        method: 'POST',
      }),
    }),
  }),
});

export const { useRegisterMutation, useLoginMutation, useLogoutMutation } = authApiSlice; 