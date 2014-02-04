import internetarchive.session


SESSION = internetarchive.session.ArchiveSession()


def get_item(identifier, **kwargs):
    return SESSION.get_item(identifier, **kwargs)

def get_file(identifier, file_name):
    item = get_item(identifier, **kwargs)
    return item.get_file(file_name)

def get_files(identifier, files, **kwargs):
    item = get_item(identifier, **kwargs)
    return item.get_files(file_name)

def download(identifier, **kwargs):
    item = get_item(identifier, **kwargs)
    return item.download(**kwargs)

def modify_metadata(identifier, metadata, **kwargs):
    item = get_item(identifier, **kwargs)
    return item.modify_metadata(metadata, **kwargs)

def upload(identifier, files, **kwargs):
    item = SESSION.get_item(identifier, **kwargs)
    return item.upload(files, **kwargs)

def delete(identifier, files, **kwargs):
    item = SESSION.get_item(identifier)
    return item.delete(files, **kwargs)

def get_tasks(**kwargs):
    catalog = SESSION.get_catalog(**kwargs)
    task_type = kwargs.get('task_type')
    if task_type:
        return eval('catalog.{0}_rows'.format(task_type.lower()))
    else:
        return catalog.tasks

def get_data_miner(identifiers, **kwargs):
    import internetarchive.mine
    return internetarchive.mine.Mine(identifiers, **kwargs)
