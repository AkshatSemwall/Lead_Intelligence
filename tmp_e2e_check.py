import asyncio
from backend.graph.workflow import get_workflow

async def main():
    workflow = get_workflow()
    initial_state = {
        'workflow_id': 'e2e-check',
        'submitted_at': '2026-07-23T00:00:00Z',
        'lead_name': 'Ava',
        'lead_email': 'ava@example.com',
        'lead_company': 'Northwind Labs',
        'lead_website': 'https://northwindlabs.com',
        'lead_phone': '1234567890',
        'lead_message': 'Please audit our company.',
        'status': 'pending',
        'current_node': None,
        'nodes_completed': [],
        'log_entries': [],
        'retry_counts': {},
        'email_sent': False,
        'progress_pct': 0,
    }
    result = await workflow.ainvoke(initial_state)
    print('STATUS', result.get('status'))
    print('CURRENT_NODE', result.get('current_node'))
    print('ERROR', result.get('error'))
    print('REPORT_EXISTS', bool(result.get('report_markdown')))
    print('REPORT_LEN', len(result.get('report_markdown') or ''))
    print('PDF_PATH', result.get('pdf_path'))
    print('DRIVE_URL', result.get('drive_url'))
    print('EMAIL_SENT', result.get('email_sent'))
    print('NODES', result.get('nodes_completed'))
    print('LOG_COUNT', len(result.get('log_entries', [])))

asyncio.run(main())
