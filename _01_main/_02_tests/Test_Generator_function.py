def my_func(last):
    i=0
    while True:
        if i>=8:
            break
        elif i==last:
            break
        else:
            yield i
            i+=1
    if not i==last:
        yield i
    
li = [j for j in my_func(last=6)]