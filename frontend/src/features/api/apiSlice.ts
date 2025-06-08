import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ 
    baseUrl: '/api',
    credentials: 'include', // This ensures cookies are sent with requests
    prepareHeaders: (headers) => {
      // The token is automatically handled by the browser via cookies
      // We don't need to manually set it in headers
      return headers;
    },
  }),
  endpoints: (builder) => ({
    // Define your endpoints here
  }),
}); 