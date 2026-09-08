# docker-ubi8

see:

* [official](https://www.redhat.com/en/blog/introducing-red-hat-universal-base-image)
* [Publickey](https://www.publickey1.jp/blog/19/red_hat_enterprise_linux_8osred_hat_universal_base_image.html)

## Quick start.

```
$ sudo docker build -t my-ubi8 -f docker-ubi8/Dockerfile .
$ sudo docker stack deploy -c docker-ubi8/docker-compose.yml dockerubi8
```

## TODO

* Can't access container with port 8000.

## See also.

* [Docker Get Started, Part 3: Services](https://docs.docker.com/get-started/part3/)
    * About docker stack.
