def from_response(request):
    result = {}
    for raw_key in request.form.keys():
        if raw_key not in ['csrf_token']:
            value = request.form.getlist(raw_key)
            key = raw_key.replace('[]', '')
            # single value as string/int
            if len(value) == 1 and '[]' not in raw_key:
                value = value[0].strip()
            if '.' not in key:
                result[key] = value
            else:
                parent_name = key.split('.')[0]
                child_name = key.split('.')[1]
                if parent_name not in result:
                    result[parent_name] = {}
                result[parent_name][child_name] = value

    return result


def validate_form_data(data, required_fields):
    errors = {}
    for field in required_fields:
        if not data.get(field, None) or not data.get(field)[0]:
            errors[field] = {"required": True}
    return errors
