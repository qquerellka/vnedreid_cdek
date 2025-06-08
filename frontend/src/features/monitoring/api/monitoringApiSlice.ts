import { apiSlice } from '../../api/apiSlice';
import type { MonitoringRequest, MonitoringResponse } from '../../../types/monitoring';

export const monitoringApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    monitor: builder.mutation<MonitoringResponse, MonitoringRequest>({
      query: (payload) => {
        const request = {
          url: '/monitoring',
          method: 'POST',
          body: payload,
        };
        console.log('RTK Query request:', {
          fullUrl: '/api' + request.url,
          method: request.method,
          body: request.body,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          }
        });
        return request;
      },
    }),
  }),
});

export const { useMonitorMutation } = monitoringApiSlice; 