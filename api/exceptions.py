from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'status': 'error',
            'errors': [],
        }
        if isinstance(response.data, dict):
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    for msg in messages:
                        custom_response_data['errors'].append({
                            'field': field,
                            'message': str(msg),
                        })
                else:
                    custom_response_data['errors'].append({
                        'field': field,
                        'message': str(messages),
                    })
        elif isinstance(response.data, list):
            custom_response_data['errors'] = [
                {'field': 'non_field_errors', 'message': str(msg)} for msg in response.data
            ]
        else:
            custom_response_data['errors'].append({
                'field': 'non_field_errors',
                'message': str(response.data),
            })
        response.data = custom_response_data

    return response
