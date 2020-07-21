# -*- coding:utf-8 -*-
from django.shortcuts import render
action = ""
modules = ""


def index(request):
    index = request.path[1:]
    global action
    global modules
    if index == "":
        return render(request, 'login.html')
    else:
        try:
            modules, action = index.split("/")
            obj = __import__("controller."+modules+"Controller", fromlist=True)
            if hasattr(obj, modules.capitalize()+"Controller"):
                controller = getattr(obj, modules.capitalize()+"Controller")()
                return getattr(controller, action)(request)
        except ValueError:
            return render(request, "404.html")
        except AttributeError:
            return render(request, "404.html")
