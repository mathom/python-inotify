#include <Python.h>
#include <sys/inotify.h>

static PyObject *init(PyObject *self, PyObject *args)
{
    PyObject *ret = NULL;
    int fd = -1;
    
     if (!PyArg_ParseTuple(args, ":init"))
	goto bail;
    
    fd = inotify_init();
    if (fd == -1) {
	PyErr_SetFromErrno(PyExc_OSError);
	goto bail;
    }
	
    ret = PyInt_FromLong(fd);
    if (ret == NULL)
	goto bail;

    goto done;
    
bail:
    if (fd != -1)
	close(fd);

    Py_XDECREF(ret);
    
done:
    return ret;
}

PyDoc_STRVAR(
    init_doc,
    "init() -> fd\n"
    "\n"
    "Initialise an inotify instance.\n"
    "Return a file descriptor associated with a new inotify event queue.");

static PyObject *add_watch(PyObject *self, PyObject *args)
{
    PyObject *ret = NULL;
    uint32_t mask;
    int wd = -1;
    char *path;
    int fd;

    if (!PyArg_ParseTuple(args, "isI:add_watch", &fd, &path, &mask))
	goto bail;

    wd = inotify_add_watch(fd, path, mask);
    if (wd == -1) {
	PyErr_SetFromErrnoWithFilename(PyExc_OSError, path);
	goto bail;
    }
    
    ret = PyInt_FromLong(wd);
    if (ret == NULL)
	goto bail;
    
    goto done;
    
bail:
    if (wd != -1)
	inotify_rm_watch(fd, wd);
    
    Py_XDECREF(ret);

done:
    return ret;
}

PyDoc_STRVAR(
    add_watch_doc,
    "add_watch(fd, path, mask) -> wd\n"
    "\n"
    "Add a watch to an inotify instance, or modify an existing watch.\n"
    "\n"
    "        fd: file descriptor returned by init()\n"
    "        path: path to watch\n"
    "        mask: mask of events to watch for\n"
    "\n"
    "Return a unique numeric watch descriptor for the inotify instance\n"
    "mapped by the file descriptor.");

static PyObject *remove_watch(PyObject *self, PyObject *args)
{
    PyObject *ret = NULL;
    uint32_t wd;
    int fd;
    int r;
    
    if (!PyArg_ParseTuple(args, "iI:remove_watch", &fd, &wd))
	goto bail;

    r = inotify_rm_watch(fd, wd);
    if (r == -1) {
	PyErr_SetFromErrno(PyExc_OSError);
	goto bail;
    }
    
    Py_INCREF(Py_None);
    
    goto done;
    
bail:
    Py_XDECREF(ret);
    
done:
    return ret;
}

PyDoc_STRVAR(
    remove_watch_doc,
    "remove_watch(fd, wd)\n"
    "\n"
    "        fd: file descriptor returned by init()\n"
    "        wd: watch descriptor returned by add_watch()\n"
    "\n"
    "Remove a watch associated with the watch descriptor wd from the\n"
    "inotify instance associated with the file descriptor fd.\n"
    "\n"
    "Removing a watch causes an IN_IGNORED event to be generated for this\n"
    "watch descriptor.");

static PyMethodDef methods[] = {
    {"init", init, METH_VARARGS, init_doc},
    {"add_watch", add_watch, METH_VARARGS, add_watch_doc},
    {"remove_watch", remove_watch, METH_VARARGS, remove_watch_doc},
    {NULL},
};
    
static char doc[] = "Low-level inotify interface wrappers.";

void init_inotify(void)
{
    PyObject *mod;

    mod = Py_InitModule3("_inotify", methods, doc);
}
