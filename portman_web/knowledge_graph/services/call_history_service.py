from ..models import CallHistory


def get_call_history(phone_number):
    histories_object = CallHistory.objects.filter(call__customer_phone=phone_number).order_by('-id')
    histories = {}

    for history_object in histories_object:
        call_id = history_object.call.id
        cluster = history_object.question.subgraph.knowledge_graph
        subject = history_object.question.subgraph
        duration = None
        if history_object.call.finished_at:
            duration = history_object.call.finished_at - history_object.call.created_at
            duration = str(duration).split('.')[0]

        if f'call_{call_id}' not in histories:
            histories[f'call_{call_id}'] = {
                'call_id': call_id,
                'date': history_object.call.created_at.strftime('%Y-%m-%d-%H:%M:%S'),
                'duration': duration,
                'need_tracking': history_object.call.need_tracking,
                'operator': {
                    'id': history_object.operator.id,
                    'username': history_object.operator.username,
                    'first_name': history_object.operator.first_name,
                    'last_name': history_object.operator.last_name,
                    'fa_first_name': history_object.operator.fa_first_name,
                    'fa_last_name': history_object.operator.fa_last_name,
                },
                'cluster': {
                    'id': cluster.id,
                    'name': cluster.name
                },
                'subjects': []
            }

        subject_found = next((s for s in histories[f'call_{call_id}']['subjects'] if s['name'] == subject.name), None)

        if subject_found is None:
            subject_found = {
                'name': subject.name,
                'id': subject.id,
                'histories': []
            }
            histories[f'call_{call_id}']['subjects'].append(subject_found)

        history = {
            'id': history_object.id,
            'question': history_object.question.context,
            'question_id': history_object.question.id,
            'answer': history_object.answer.relation if history_object.answer else None,
            'description': history_object.description,
            'next_question': history_object.answer.to_node.context if history_object.answer and history_object.answer.to_node else None,
            'next_question_id': history_object.answer.to_node.id if history_object.answer and history_object.answer.to_node else None,
            'date': history_object.created_at.strftime('%Y-%m-%d-%H:%M:%S'),
        }
        subject_found['histories'].append(history)

    return [value for key, value in histories.items()]