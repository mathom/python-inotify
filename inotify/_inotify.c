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

static void define_const(PyObject *dict, const char *name, uint32_t val)
{
    PyObject *pyval = PyInt_FromLong(val);
    PyObject *pyname = PyString_FromString(name);

    if (pyname && pyval)
	PyDict_SetItem(dict, pyname, pyval);

    Py_XDECREF(pyname);
    Py_XDECREF(pyval);
}

static void define_consts(PyObject *dict)
{
#ifdef IN_ACCESS
    define_const(dict, "IN_ACCESS", IN_ACCESS);
#endif
#ifdef IN_MODIFY
    define_const(dict, "IN_MODIFY", IN_MODIFY);
#endif
#ifdef IN_ATTRIB
    define_const(dict, "IN_ATTRIB", IN_ATTRIB);
#endif
#ifdef IN_CLOSE_WRITE
    define_const(dict, "IN_CLOSE_WRITE", IN_CLOSE_WRITE);
#endif
#ifdef IN_CLOSE_NOWRITE
    define_const(dict, "IN_CLOSE_NOWRITE", IN_CLOSE_NOWRITE);
#endif
#ifdef IN_CLOSE
    define_const(dict, "IN_CLOSE", IN_CLOSE);
#endif
#ifdef IN_OPEN
    define_const(dict, "IN_OPEN", IN_OPEN);
#endif
#ifdef IN_MOVED_FROM
    define_const(dict, "IN_MOVED_FROM", IN_MOVED_FROM);
#endif
#ifdef IN_MOVED_TO
    define_const(dict, "IN_MOVED_TO", IN_MOVED_TO);
#endif
#ifdef IN_MOVE
    define_const(dict, "IN_MOVE", IN_MOVE);
#endif
#ifdef IN_CREATE
    define_const(dict, "IN_CREATE", IN_CREATE);
#endif
#ifdef IN_DELETE
    define_const(dict, "IN_DELETE", IN_DELETE);
#endif
#ifdef IN_DELETE_SELF
    define_const(dict, "IN_DELETE_SELF", IN_DELETE_SELF);
#endif
#ifdef IN_MOVE_SELF
    define_const(dict, "IN_MOVE_SELF", IN_MOVE_SELF);
#endif

#ifdef IN_UNMOUNT
    define_const(dict, "IN_UNMOUNT", IN_UNMOUNT);
#endif
#ifdef IN_Q_OVERFLOW
    define_const(dict, "IN_Q_OVERFLOW", IN_Q_OVERFLOW);
#endif
#ifdef IN_IGNORED
    define_const(dict, "IN_IGNORED", IN_IGNORED);
#endif

#ifdef IN_CLOSE
    define_const(dict, "IN_CLOSE", IN_CLOSE);
#endif
#ifdef IN_MOVE
    define_const(dict, "IN_MOVE", IN_MOVE);
#endif

#ifdef IN_ONLYDIR
    define_const(dict, "IN_ONLYDIR", IN_ONLYDIR);
#endif

#ifdef IN_DONT_FOLLOW
    define_const(dict, "IN_DONT_FOLLOW", IN_DONT_FOLLOW);
#endif
#ifdef IN_MASK_ADD
    define_const(dict, "IN_MASK_ADD", IN_MASK_ADD);
#endif

#ifdef IN_ISDIR
    define_const(dict, "IN_ISDIR", IN_ISDIR);
#endif
#ifdef IN_ONESHOT
    define_const(dict, "IN_ONESHOT", IN_ONESHOT);
#endif

#ifdef IN_ALL_EVENTS
    define_const(dict, "IN_ALL_EVENTS", IN_ALL_EVENTS);
#endif
}

void init_inotify(void)
{
    PyObject *mod, *dict;

    mod = Py_InitModule3("_inotify", methods, doc);

    dict = PyModule_GetDict(mod);
    
    if (dict)
	define_consts(dict);
}
