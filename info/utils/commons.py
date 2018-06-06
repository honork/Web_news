

# 自定义过滤器，用来对模板页面进行处理处理
def index_class(index):
    if index == 0:
        return 'first'
    elif index == 1:
        return 'second'
    elif index == 2:
        return 'third'
    else:
        return ''



