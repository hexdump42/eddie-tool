/*
** File        : solkstatmodule.c
**
** Date        : 980713
**
** Author      : Rod Telford <rtelford@connect.com.au>
**
** Description : This module provides a binding between 
**               the Solaris kstat library and Python
**
** $Id$
**
*/

#include "Python.h"
#include <kstat.h>

static PyObject *ErrorObject;

static PyObject *PyLong_FromLongLong(long long v);
static PyObject *build_io_data(kstat_t *kp);

/* ----------------------------------------------------- */

/* Declarations for objects of type kstatistics */

typedef struct {
    PyObject_HEAD
    
    kstat_t *kp;
    kstat_ctl_t *kc;

} kstatobject;

staticforward PyTypeObject Kstattype;



/* ---------------------------------------------------------------- */

static kstatobject *
newkstatobject(kc, curr)
    kstat_ctl_t *kc;
    kstat_t *curr;
{
    kstatobject *self;
    
    self = PyObject_NEW(kstatobject, &Kstattype);
    if (self == NULL)
	return NULL;

    self->kc = kc;
    self->kp = curr;

    return self;
}


static char kstat_getnext__doc__[] = 
""
;

static PyObject *
kstat_getnext(self, args)
    kstatobject *self;
    PyObject *args;
{
    PyObject *ret;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    if(self->kp->ks_next) 
    {
        ret = (PyObject *)newkstatobject(self->kc, self->kp->ks_next);
        return ret;
    }
    else
    {
	Py_INCREF(Py_None);
	return Py_None;
    }
}

static char kstat_lookup__doc__[] =
""
;

static PyObject *
kstat_find(self, args)
    kstatobject *self;
    PyObject *args;
{
    PyObject *ret;
    kstat_t *kp;

    char *ks_modual;
    int ks_instance;
    char *ks_name;

    if (!PyArg_ParseTuple(args, "sis", &ks_modual, &ks_instance, &ks_name))
	return NULL;

    kp = kstat_lookup(self->kc, ks_modual, ks_instance, ks_name);

    ret = (PyObject *)newkstatobject(self->kc, kp);
    return ret;
}

/*
static char kstat_getdata__doc__[] =
""
;

static PyObject *
kstat_getdata(self, args)
    kstatobject *self;
    PyObject *args;
{
    if ( kstat_read(self->kc, self->kp, 0) != -1 )
}
*/


static struct PyMethodDef kstat_methods[] = {
    {"getnext",	(PyCFunction)kstat_getnext,	METH_VARARGS,	kstat_getnext__doc__},
    {"lookup",	(PyCFunction)kstat_find,	METH_VARARGS,	kstat_lookup__doc__},
 /*   {"getdata",	(PyCFunction)kstat_getdata,	METH_VARARGS,	kstat_getdata__doc__}, */
    {NULL,		NULL}		/* sentinel */
};

/* ---------- */



static void
kstat_dealloc(self)
    kstatobject *self;
{
    /* XXXX Add your own cleanup code here */

    PyMem_DEL(self);
}

static PyObject *
kstat_str(self)
    kstatobject *self;
{
    PyObject *s;

    /* XXXX Add code here to put self into s */
    s = Py_BuildValue("(sss)", self->kp->ks_module, self->kp->ks_name, self->kp->ks_class);

    return s;
}


/* Code to access structure members by accessing attributes */

#include "structmember.h"

#define OFF(x) offsetof(XXXXobject, x)

static struct memberlist kstat_memberlist[] = {
    /* XXXX Add lines like { "foo", T_INT, OFF(foo), RO }  */

    {NULL}	/* Sentinel */
};

static PyObject *
kstat_getattr(self, name)
    kstatobject *self;
    char *name;
{
    PyObject *rv;

    /* do we want the name attribute */

    if( strcmp(name, "ks_crtime") == 0 )
	return PyLong_FromLongLong(self->kp->ks_crtime);

    if( strcmp(name, "ks_name") == 0 )
	return Py_BuildValue("s", self->kp->ks_name);

    if( strcmp(name, "ks_kid") == 0 )
	return Py_BuildValue("l", self->kp->ks_kid);

    if( strcmp(name, "ks_instance") == 0 )
	return Py_BuildValue("i", self->kp->ks_instance);

    if( strcmp(name, "ks_type") == 0 )
	return Py_BuildValue("i", (int)self->kp->ks_type);

    if( strcmp(name, "ks_class") == 0 )
	return Py_BuildValue("s", self->kp->ks_class);

    if( strcmp(name, "ks_module") == 0 )
	return Py_BuildValue("s", self->kp->ks_module);

    if( strcmp(name, "ks_flags") == 0 )
	return Py_BuildValue("i", self->kp->ks_flags);

    /* Here is one for KSTAT_TYPE_IO */
    if( strcmp(name, "ks_data") == 0 )  
    {
	/* data type KSTAT_TYPE_IO */
	switch(self->kp->ks_type)
	{
	    case KSTAT_TYPE_IO:
		if ( kstat_read(self->kc, self->kp, 0) != -1 )
		    return build_io_data(self->kp);
	}
    }

    if( strcmp(name, "ks_ndata") == 0 )
	return PyLong_FromUnsignedLong(self->kp->ks_ndata);

    if( strcmp(name, "ks_data_size") == 0 )
	return PyLong_FromUnsignedLong(self->kp->ks_data_size);

    if( strcmp(name, "ks_snaptime") == 0 )
	return PyLong_FromLongLong(self->kp->ks_snaptime);

    rv = PyMember_Get((char *)/*XXXX*/0, kstat_memberlist, name);
    if (rv)
	    return rv;
    PyErr_Clear();
    return Py_FindMethod(kstat_methods, (PyObject *)self, name);
}


static int
kstat_setattr(self, name, v)
    kstatobject *self;
    char *name;
    PyObject *v;
{
    /* XXXX Add your own setattr code here */
    if ( v == NULL ) {
	PyErr_SetString(PyExc_AttributeError, "Cannot delete attribute");
	return -1;
    }
    return PyMember_Set((char *)/*XXXX*/0, kstat_memberlist, name, v);
}


static char Kstattype__doc__[] = 
""
;

static PyTypeObject Kstattype = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,					/*ob_size*/
    "kstatistics",			/*tp_name*/
    sizeof(kstatobject),		/*tp_basicsize*/
    0,					/*tp_itemsize*/
    /* methods */
    (destructor)kstat_dealloc,		/*tp_dealloc*/
    (printfunc)0,			/*tp_print*/
    (getattrfunc)kstat_getattr,		/*tp_getattr*/
    (setattrfunc)kstat_setattr,		/*tp_setattr*/
    (cmpfunc)0,				/*tp_compare*/
    (reprfunc)kstat_str,		/*tp_repr*/
    0,					/*tp_as_number*/
    0,					/*tp_as_sequence*/
    0,					/*tp_as_mapping*/
    (hashfunc)0,			/*tp_hash*/
    (ternaryfunc)0,			/*tp_call*/
    (reprfunc)kstat_str,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Kstattype__doc__ 			/* Documentation string */
};

/* End of code for kstatistics objects */
/* -------------------------------------------------------- */


static char skstat_open__doc__[] =
""
;

static PyObject *
skstat_open(self, args)
    PyObject *self;	/* Not used */
    PyObject *args;
{
    PyObject *ret;
    kstat_ctl_t *kc;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    kc = kstat_open();

    /*
    Py_Assert( kc != 0, ErrorObject, "Can't open kstat tree" );
    */
    
    ret = (PyObject *)newkstatobject(kc, kc->kc_chain);

    kstat_close(kc);
	
    return ret;
}

/* List of methods defined in the module */

static struct PyMethodDef skstat_methods[] = {
    {"open",	(PyCFunction)skstat_open,	METH_VARARGS,	skstat_open__doc__},
    {NULL,	 (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initsolkstat) */

static char solkstat_module_documentation[] = 
""
;

void
initsolkstat()
{
    PyObject *m, *d;

    /* Create the module and add the functions */
    m = Py_InitModule4("solkstat", skstat_methods,
	solkstat_module_documentation,
	(PyObject*)NULL,PYTHON_API_VERSION);

    /* Add some symbolic constants to the module */
    d = PyModule_GetDict(m);
    ErrorObject = PyString_FromString("solkstat.error");
    PyDict_SetItemString(d, "error", ErrorObject);

    /* XXXX Add constants here */
    
    /* Check for errors */
    if (PyErr_Occurred())
	Py_FatalError("can't initialize module solkstat");
}


/* Now for my routines */
static PyObject *
build_io_data(kp)
    kstat_t *kp;
{
    kstat_io_t	*rec;

    if (!kp || !kp->ks_data)
    {
	Py_INCREF(Py_None);
	return Py_None;
    }

    rec = kp->ks_data;

    return (Py_BuildValue("{s:O, s:O, s:O, s:O, s:O, s:O, s:O, s:O, s:O, s:O, s:O, s:O}",
	                 "nread",       PyLong_FromLongLong(rec->nread),
	                 "nwritten",    PyLong_FromLongLong(rec->nwritten),
	                 "reads",       PyLong_FromLong(rec->reads),
	                 "writes",      PyLong_FromLong(rec->writes),
	                 "wtime",       PyLong_FromLongLong(rec->wtime),
	                 "wlentime",    PyLong_FromLongLong(rec->wlentime),
	                 "wlastupdate", PyLong_FromLongLong(rec->wlastupdate),
	                 "rtime",       PyLong_FromLongLong(rec->rtime),
	                 "rlentime",    PyLong_FromLongLong(rec->rlentime),
	                 "rlastupdate", PyLong_FromLongLong(rec->rlastupdate),
	                 "wcnt",        PyLong_FromUnsignedLong(rec->wcnt),
	                 "rcnt",        PyLong_FromUnsignedLong(rec->rcnt) ));

}


static PyObject *
PyLong_FromLongLong(long long v)
{
	/* XXXX Somewhat complicated way to convert a long long to a PyLong */
	PyObject *l = NULL, *lhi, *llo;
	int is_negative = 0;
	static PyObject *i32;	/* 32 as a python long */

	if (v < 0) {
		is_negative = 1;
		v = -v;
	}
	lhi = PyLong_FromUnsignedLong((unsigned long) ((unsigned long long) v >> 32));
	llo = PyLong_FromUnsignedLong((unsigned long) (v & 0xFFFFFFFFLL));
	if (i32 == NULL)
		i32 = PyLong_FromLong(32L); /* don't decref */
	if (PyErr_Occurred())
		goto error;
	if ((l = PyNumber_Lshift(lhi, i32)) == NULL)
		goto error;
	Py_DECREF(lhi);
	lhi = l;
	if ((l = PyNumber_Or(lhi, llo)) == NULL)
		goto error;
	Py_DECREF(lhi);
	Py_DECREF(llo);
	if (is_negative) {
		if ((lhi = PyNumber_Negative(l)) == NULL)
			goto error;
		Py_DECREF(l);
		l = lhi;
	}
	return l;

  error:
	Py_XDECREF(lhi);
	Py_XDECREF(llo);
	Py_XDECREF(l);
	return NULL;
}

