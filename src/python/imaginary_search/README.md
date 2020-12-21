## Intro

Imagine that you are involved in the development of a large file storage system. Special feature here is storing photos and images. We need to provide our users with the possibility to search stored images based on attribute fields.


## Requirements


We need to see your own code.

The app should load and cache photos from our API endpoint http://interview.agileengine.com

Obtain a valid Bearer token with valid API key (don't forget to implement invalid token handler and renewal)
POST http://interview.agileengine.com/auth
Body: { "apiKey": "23567b218376f79d9415" }
Response: { "token": "ce09287c97bf310284be3c97619158cfed026004" }

The app should fetch paginated photo feed in JSON format with the following REST API call (GET):
GET /images
Headers: Authorization: Bearer ce09287c97bf310284be3c97619158cfed026004

Following pages can be retrieved by appending ‘page=N’ parameter:
GET /images?page=2

No redundant REST API calls should be triggered by the app.

The app should fetch more photo details (photographer name, better resolution, hashtags) by the following REST API call (GET):
GET /images/${id}

The app should fetch the entire load of images information upon initialization and perform cache reload once in a defined (configurable) period of time.

The app should provide a new endpoint: GET /search/${searchTerm}, that will return all the photos with any of the meta fields (author, camera, tags, etc) matching the search term. The info should be fetched from the local cache, not the external API.

You are free to choose the way you maintain local cache (any implementation of the cache, DB, etc). The search algorithm, however, should be implemented by you.

We value code readability and consistency, and usage of modern community best practices and architectural approaches, as well, as functionality correctness. So pay attention to code quality.

Target completion time is about 2 hours. We would rather see what you were able to do in 2 hours than a full-blown algorithm you’ve spent days implementing. Note that in addition to quality, time used is also factored into scoring the task.


## Expected Deliverables


Source code.
Readme, with instructions, how to build and run.


# Steps

## 1. Navigate yourself

Clone monorepo and cd into its root dir
```
$ git clone https://github.com/IrSent/imaginary_monorepo imaginary_monorepo/
$ cd imaginary_monorepo/
```

## 2. Install Pants:

```
curl -L -o ./pants https://pantsbuild.github.io/setup/pants && \
chmod +x ./pants
```

## 3. Run pex_binary target
```
$ ./pants run src/python/imaginary_search:service
```
