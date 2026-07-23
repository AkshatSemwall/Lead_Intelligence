import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export const submitLead = (data) =>
  api.post('/submit-lead', data).then((r) => r.data)

export const getWorkflowStatus = (workflowId) =>
  api.get(`/workflow-status/${workflowId}`).then((r) => r.data)

export const getReport = (workflowId) =>
  api.get(`/report/${workflowId}`).then((r) => r.data)

export const getWorkflowLogs = (workflowId) =>
  api.get(`/logs/${workflowId}`).then((r) => r.data)

export const listWorkflows = () =>
  api.get('/workflows').then((r) => r.data)

export const getHealth = () =>
  api.get('/health').then((r) => r.data)

export const getPdfUrl = (workflowId) => `/api/report/${workflowId}/pdf`

export default api
