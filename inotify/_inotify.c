#include <Python.h>
#include <sys/inotify.h>

static PyObject *pyinotify_init(PyObject *self, PyObject *args)
{
    PyObject *ret = NULL;
    int fd = -1;
    
    if (!PyArg_ParseTuple(args, ":init"))
	goto bail;
    
    fd = inotify_init();

    if (fd == -1) {
	printf("bail\n");
	ret = PyErr_SetFromErrno(PyExc_OSError);
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

static char init_doc[] =
    "Initialise an inotify instance.\n"
    "Returns a file descriptor associated with a new inotify event queue.";

static PyMethodDef methods[] = {
    {"init", pyinotify_init, METH_VARARGS, init_doc},
    {NULL},
};
    
static char doc[] = "Low-level inotify interface wrappers.";

void init_inotify(void)
{
    PyObject *mod;

    mod = Py_InitModule3("_inotify", methods, doc);
}
