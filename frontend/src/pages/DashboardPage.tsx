import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody, Spinner, Input, Button, Select, SelectItem, Table, TableHeader, TableColumn, TableBody, TableRow, TableCell } from '@heroui/react';
import ReactECharts from 'echarts-for-react';
import { useMonitorMutation } from '../features/monitoring/api/monitoringApiSlice';
import type { MonitoringRequest, MonitoringResponse, Vacancy } from '../types/monitoring';
import type { FetchBaseQueryError } from '@reduxjs/toolkit/query';

interface ErrorResponse {
  detail: string;
}

const DashboardPage: React.FC = () => {
  const [position, setPosition] = useState('');
  const [salary, setSalary] = useState('');
  const [region, setRegion] = useState('');
  const [experience, setExperience] = useState('');
  const [monitoringResults, setMonitoringResults] = useState<MonitoringResponse | null>(null);

  const [monitor, { isLoading: isMonitoring, error: monitorError }] = useMonitorMutation();

  const handleMonitor = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Log the form data before sending
    const requestData = {
      position,
      salary: parseInt(salary),
      region,
      experience,
    };
    console.log('Sending monitoring request with data:', requestData);
    console.log('API endpoint: /api/monitoring');
    console.log('Request method: POST');
    
    try {
      console.log('Making API call...');
      const result = await monitor(requestData).unwrap();
      console.log('Received response:', result);
      setMonitoringResults(result);
    } catch (err: unknown) {
      console.error('API call failed:', err);
      if (err && typeof err === 'object' && 'status' in err) {
        const fetchError = err as FetchBaseQueryError;
        const errorData = fetchError.data as ErrorResponse | undefined;
        console.error('Error details:', {
          status: fetchError.status,
          data: errorData,
          message: 'status' in fetchError ? String(fetchError.status) : 'Unknown error'
        });
        alert(`Error: ${errorData?.detail || 'Something went wrong'}`);
      } else {
        console.error('Unknown error type:', err);
        alert('An unexpected error occurred');
      }
    }
  };

  // Log when component mounts and when state changes
  useEffect(() => {
    console.log('Current form state:', {
      position,
      salary,
      region,
      experience,
      isMonitoring,
      hasResults: !!monitoringResults
    });
  }, [position, salary, region, experience, isMonitoring, monitoringResults]);

  const getChartOption = () => {
    if (!monitoringResults) {
      return {};
    }
    return {
      title: {
        text: 'Vacancies Found',
        left: 'center',
        textStyle: {
          color: '#333',
        },
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      xAxis: {
        type: 'category',
        data: ['Vacancies'],
        axisLabel: {
          color: '#555',
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#555',
        },
      },
      series: [
        {
          name: 'Count',
          type: 'bar',
          data: [monitoringResults.vacancies_found],
          itemStyle: {
            color: '#4299e1', // Tailwind blue-500
          },
        },
      ],
    };
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 md:p-12 lg:p-16">
      <h1 className="text-4xl lg:text-5xl font-extrabold text-gray-900 mb-4">Dashboard</h1>
      <p className="text-lg text-gray-600 mb-10">Welcome to your personalized dashboard. Explore insights and run new monitoring requests with ease.</p>

      {/* Monitoring Request Card */}
      <Card className="mb-12 rounded-xl shadow-lg bg-white">
        <CardHeader className="p-6 border-b border-gray-200">
          <h3 className="text-2xl font-semibold text-gray-800">Run New Monitoring Request</h3>
        </CardHeader>
        <CardBody className="p-6 lg:p-8">
          <form onSubmit={handleMonitor} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Input
              label="Position"
              placeholder="e.g., Python Developer"
              value={position}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPosition(e.target.value)}
              required
              fullWidth
              variant="bordered"
              size="lg"
            />
            <Input
              type="number"
              label="Desired Salary"
              placeholder="e.g., 100000"
              value={salary}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSalary(e.target.value)}
              required
              fullWidth
              variant="bordered"
              size="lg"
            />
            <Input
              label="Region"
              placeholder="e.g., Москва"
              value={region}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRegion(e.target.value)}
              required
              fullWidth
              variant="bordered"
              size="lg"
            />
            <Select
              label="Experience"
              placeholder="Select experience level"
              selectedKeys={[experience]}
              onSelectionChange={(keys) => setExperience(Array.from(keys).join(''))}
              required
              fullWidth
              variant="bordered"
              size="lg"
            >
              <SelectItem key="Нет опыта">No experience</SelectItem>
              <SelectItem key="От 1 года до 3 лет">1-3 years</SelectItem>
              <SelectItem key="От 3 до 6 лет">3-6 years</SelectItem>
              <SelectItem key="Более 6 лет">More than 6 years</SelectItem>
            </Select>
            <div className="md:col-span-2 lg:col-span-4 flex justify-end mt-4">
              <Button
                type="submit"
                color="primary"
                size="lg"
                isLoading={isMonitoring}
                disabled={isMonitoring}
                className="w-full md:w-auto px-8 py-3 text-lg font-semibold rounded-lg shadow-md hover:shadow-lg transition-all duration-300 transform hover:scale-105"
              >
                {isMonitoring ? (
                  <div className="flex items-center"><Spinner size="sm" color="current" className="mr-2" /> Running Monitoring...</div>
                ) : (
                  'Run Monitoring'
                )}
              </Button>
            </div>
          </form>
          {monitorError && (
            <p className="text-red-500 mt-6 text-center text-sm font-medium p-3 bg-red-50 rounded-lg border border-red-200">
              Error: {JSON.stringify(monitorError.data?.detail || 'Something went wrong')}
            </p>
          )}
        </CardBody>
      </Card>

      {monitoringResults && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Monitoring Summary Card */}
          <Card className="lg:col-span-1 rounded-xl shadow-lg bg-white">
            <CardHeader className="p-6 border-b border-gray-200">
              <h3 className="text-2xl font-semibold text-gray-800">Monitoring Summary</h3>
            </CardHeader>
            <CardBody className="p-6 flex flex-col items-center justify-center">
              <p className="text-4xl font-bold text-blue-600 mb-4">{monitoringResults.vacancies_found}</p>
              <p className="text-xl text-gray-700">Vacancies Found</p>
              <div className="mt-6 w-full">
                <ReactECharts option={getChartOption()} style={{ height: 300, width: '100%' }} />
              </div>
            </CardBody>
          </Card>

          {/* Vacancies Details Table */}
          <Card className="lg:col-span-2 rounded-xl shadow-lg bg-white">
            <CardHeader className="p-6 border-b border-gray-200">
              <h3 className="text-2xl font-semibold text-gray-800">Vacancies Details</h3>
            </CardHeader>
            <CardBody className="p-6 overflow-x-auto">
              {monitoringResults.vacancies.length > 0 ? (
                <Table aria-label="Vacancies Table" selectionMode="single" className="min-w-full divide-y divide-gray-200">
                  <TableHeader>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Position</TableColumn>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</TableColumn>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Salary</TableColumn>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Region</TableColumn>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Experience</TableColumn>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Published At</TableColumn>
                    <TableColumn className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Link</TableColumn>
                  </TableHeader>
                  <TableBody className="bg-white divide-y divide-gray-200">
                    {monitoringResults.vacancies.map((vacancy: Vacancy) => (
                      <TableRow key={vacancy.id}>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{vacancy.name}</TableCell>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{vacancy.company_name}</TableCell>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                          {vacancy.salary_from && vacancy.salary_to
                            ? `$${vacancy.salary_from} - $${vacancy.salary_to}`
                            : vacancy.salary_from
                              ? `From $${vacancy.salary_from}`
                              : vacancy.salary_to
                                ? `Up to $${vacancy.salary_to}`
                                : 'N/A'}
                        </TableCell>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{vacancy.region}</TableCell>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{vacancy.experience}</TableCell>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{new Date(vacancy.published_at).toLocaleDateString()}</TableCell>
                        <TableCell className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <a href={vacancy.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 hover:underline">View</a>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-gray-600 p-4">No vacancies found for this request. Try adjusting your criteria.</p>
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DashboardPage; 