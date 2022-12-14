import base64
import json
import mimetypes

import requests
from hashlib import md5

from numpy import random

from .content import get_content, get_content_informations, get_content_mimetype, post_node_children, \
  put_content_node
from .count import count_sites, count_tags, count_people, count_groups, count_documents
from .people import get_peoples, get_people_id, get_people_avatar, get_people_activities
from .search import run_query, run_query_cmis
from .utils import percentage, clear_database, check_token
from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View

from .compat import is_authenticated
from .forms import DocumentForm
from .models import Document, Activity


import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np

############################################
# PAGES
############################################
def index(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  counter_sites = count_sites(password)
  counter_tags = count_tags(password)
  counter_people = count_people(password)
  counter_groups = count_groups(password)
  counter_documents =count_documents(password)

  percent_sites = percentage(counter_sites, 100)
  percent_tags = percentage(counter_tags, 100)
  percent_people = percentage(counter_people, 100)
  percent_groups = percentage(counter_groups, 100)

  result_list_last_documents = []
  query = "Select * from cmis:document ORDER BY cmis:creationDate DESC"
  result_list_last_documents = run_query_cmis(query, password, 10)

  peoples = get_peoples("8")
  peoples = peoples.json()
  peoples = peoples['list']['entries']

  labels = 'Sites', 'Documents'
  sizes = [counter_sites, counter_documents]
  explode = (0.1, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')

  fig1, ax1 = plt.subplots()
  ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
          shadow=True, startangle=90)
  ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
  plt.savefig('djangoalfresco/static/images/sale_purchase_peichart.png', dpi=100)

  return render(request, "adminlte/index.html",
                {
                  'build_page_title': 'Alfresco Django',
                  'count_sites': counter_sites,
                  'count_tags': counter_tags,
                  'count_people': counter_people,
                  'count_groups': counter_groups,
                  'percent_sites': percent_sites,
                  'percent_tags': percent_tags,
                  'percent_people': percent_people,
                  'percent_groups': percent_groups,
                  'result_list': result_list_last_documents,
                  'peoples': peoples,
                  'counter_documents':counter_documents,
                })

def profile(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  user = get_people_id(password, request.user.username)
  activities = get_people_activities(password, request.user.username, "10")
  activities = activities.json()
  activities = activities['list']['entries']

  for activity in activities:
    act = Activity.objects.get(code=activity['entry']['activityType'])
    activity['entry']['activity'] = act.title

  return render(request, 'adminlte/profile.html', {
    'build_page_title': 'Alfresco Django - User Profile',
    'user': user.json(),
    'activities': activities,
    'avatar': avatar,
    'title': 'User Profile'
  })


def sites(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  default_params = "?skipCount=0&maxItems=100"

  auth = bytes('Basic ', "utf-8")
  headers = {'Accept': 'application/json', 'Authorization': auth + base64.b64encode(bytes(password, "utf-8"))}

  response = requests.get(settings.URL_CORE + settings.URL_SITES + default_params, headers=headers)
  content = response.json()

  return render(request, 'adminlte/sites.html', {
    'build_page_title': 'Alfresco Django - Sites',
    'status': response.status_code,
    'title': 'List of Sites',
    'sites': content['list']['entries'],
  })


def tags(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  default_params = "?skipCount=0&maxItems=100"

  auth = bytes('Basic ', "utf-8")
  headers = {'Accept': 'application/json', 'Authorization': auth + base64.b64encode(bytes(password, "utf-8"))}

  response = requests.get(settings.URL_CORE + settings.URL_TAGS + default_params, headers=headers)
  content = response.json()

  return render(request, 'adminlte/tags.html', {
    'build_page_title': 'Alfresco Django - Tags',
    'status': response.status_code,
    'title': 'List of Tags',
    'tags': content['list']['entries'],
  })


def people(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  default_params = "?skipCount=0&maxItems=100"

  auth = bytes('Basic ', "utf-8")
  headers = {'Accept': 'application/json', 'Authorization': auth + base64.b64encode(bytes(password, "utf-8"))}

  response = requests.get(settings.URL_CORE + settings.URL_PEOPLE + default_params, headers=headers)
  content = response.json()

  return render(request, 'adminlte/people.html', {
    'build_page_title': 'Alfresco Django - People',
    'status': response.status_code,
    'title': 'List of People',
    'people': content['list']['entries'],
  })


def groups(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  default_params = "?skipCount=0&maxItems=100"

  auth = bytes('Basic ', "utf-8")
  headers = {'Accept': 'application/json', 'Authorization': auth + base64.b64encode(bytes(password, "utf-8"))}

  response = requests.get(settings.URL_CORE + settings.URL_GROUPS + default_params, headers=headers)
  content = response.json()

  return render(request, 'adminlte/groups.html', {
    'build_page_title': 'Alfresco Django - Groups',
    'status': response.status_code,
    'title': 'List of Groups',
    'groups': content['list']['entries'],
  })


def search(request):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  result_list = []

  if request.method == 'POST':
    query = request.POST['query'].strip()

    if query:
      result_list = run_query(query, password)

  return render(request, 'adminlte/search.html', {
    'build_page_title': 'Alfresco Django - Search',
    'result_list': result_list})


def viewer(request, nodeId):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  return render(request, 'adminlte/viewer.html', {
    'build_page_title': 'Alfresco Django - Viewer',
    'nodeId': nodeId})


def content(request, nodeId):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  content = get_content(nodeId, password)
  response = HttpResponse(content)
  mimetype = get_content_mimetype(nodeId, password)
  response['Content-Type'] = mimetype
  return response


def avatar(request, userId):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  if userId != None:
    content = get_people_avatar(password, userId)
  else:
    content = get_people_avatar(password, request.user.username)

  if content.status_code == 200:
    response = HttpResponse(content)
    response['Content-Type'] = 'image/png'
    return response
  else:
    return 'https://www.gravatar.com/avatar/{hash}?s={size}&d=mm'.format(
      hash=md5(user.email.encode('utf-8')).hexdigest() if is_authenticated(user) else '', size=size or '',
    )


def content_json(request, nodeId):
  password = check_token(request)

  if password == None:
    logout(request)
    return HttpResponseRedirect("/login")

  content = get_content_informations(nodeId, password)
  content = json.dumps(content, indent=4, sort_keys=True)

  response = HttpResponse(content)
  response['Content-Type'] = 'application/json'
  return response


class BasicUploadView(View):
  def get(self, request):
    documents_list = Document.objects.all()
    return render(self.request, 'adminlte/basic-upload.html',
                  {'build_page_title': 'Alfresco Django - Upload', 'documents': documents_list})

  def post(self, request):

    form = DocumentForm(self.request.POST, self.request.FILES)
    file = self.request.FILES

    if form.is_valid():
      password = check_token(request)
      if password == None:
        logout(request)
        return HttpResponseRedirect("/login")

      document = form.save()
      file_mime = mimetypes.guess_type(document.file.url)[0]
      response = post_node_children("-my-", document.file.name, password)

      if response.status_code == 201:
        children = response.json()
        put_content_node(children['entry']['id'], "media/" + document.file.name, password)

      data = {'is_valid': True, 'name': document.file.name, 'url': document.file.url}
      clear_database()
    else:
      data = {'is_valid': False}
    return JsonResponse(data)

