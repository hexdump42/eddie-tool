/*
** File        : solkstatmodule.c
**
** Date        : 980713
**
** Author      : Rod Telford <rtelford@connect.com.au>
**               Chris Miles <chris@psychofx.com>
**
** Description : This module provides a binding between 
**               the Solaris kstat library and Python
**
** $Id$
**
*/

#include "Python.h"
#include <kstat.h>

#include "structmember.h"

#define OFF(x) offsetof(XXXXobject, x)

static PyObject *ErrorObject;

/*
static PyObject *PyLong_FromLongLong(long long v);
*/

static PyObject *build_io_data(kstat_t *kp);

/* ----------------------------------------------------- */

/* Declarations for objects of type kstatistics */

/* kstatnamed: a representation of kstat_named_t which holds named kstat
 * data as returned from kstat_data_lookup()
 */

typedef struct {
    PyObject_HEAD

    kstat_named_t *kn;
} kstatnamed;


/*
 * kstatobject: really a kstat_ctl_t pointer.  Represents each
 * node of kstat linked list.
 */

typedef struct {
    PyObject_HEAD
    
    kstat_t *kp;
    kstat_ctl_t *kc;

} kstatobject;

/*
 * kstatdataobject: really a kstat_t pointer.  Represents kstat data
 * returned from kstat_lookup() etc.
 */

typedef struct {
    PyObject_HEAD
    
    kstat_ctl_t *kc;
    kstat_t *ksp;

} kstatdataobject;


staticforward PyTypeObject Kstattype;
staticforward PyTypeObject Kstatdatatype;
staticforward PyTypeObject Kstatnamedtype;



/* ---------------------------------------------------------------- */

static kstatnamed *
newkstatnamed(kn)
    kstat_named_t *kn;
{
    kstatnamed *self;
    
    self = PyObject_NEW(kstatnamed, &Kstatnamedtype);
    if (self == NULL)
	return NULL;

    self->kn = kn;

    return self;
}

static void
kstatnamed_dealloc(self)
    kstatnamed *self;
{
    /* XXXX Add your own cleanup code here */

    PyMem_DEL(self);
}

static PyObject *
kstatnamed_str(self)
    kstatnamed *self;
{
    PyObject *s;
    char str[256];

    snprintf( str, 256, "%s", self->kn->name );
    s = PyString_FromString(str);

    /*
    if( self->kn != NULL )
	if( self->kn->name != NULL )
	    s = Py_BuildValue("(s)", self->kn->name);
	else
	    s = Py_None;
    else
	s = Py_None;
    */

    return s;
}

static char kstatnamed_getdata__doc__[] =
""
;

static PyObject *
kstatnamed_getdata(self, args)
    kstatnamed *self;
    PyObject *args;
{
    PyObject *ret;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    if( self->kn == NULL )
	return NULL;

    switch( self->kn->data_type ) {
	case KSTAT_DATA_CHAR:
	    ret = PyString_FromString(self->kn->value.c);	/* actually a string... XXXX */
	    break;
	case KSTAT_DATA_INT32:
	    ret = PyLong_FromLong(self->kn->value.i32);
	    break;
	case KSTAT_DATA_UINT32:
	    ret = PyLong_FromLong(self->kn->value.ui32);
	    break;
	case KSTAT_DATA_INT64:
	    ret = PyLong_FromLongLong(self->kn->value.i64);
	    break;
	case KSTAT_DATA_UINT64:
	    ret = PyLong_FromLongLong(self->kn->value.ui64);
	    break;
	default:
	    ret = Py_None;
    }

    return (PyObject*)ret;
}


static struct PyMethodDef kstatnamed_methods[] = {
    {"getdata",		(PyCFunction)kstatnamed_getdata,	METH_VARARGS,	kstatnamed_getdata__doc__},
    {NULL,		NULL}		/* sentinel */
};

static struct memberlist kstatnamed_memberlist[] = {
    /* XXXX Add lines like { "foo", T_INT, OFF(foo), RO }  */

    {NULL}	/* Sentinel */
};


static PyObject *
kstatnamed_getattr(self, name)
    kstatnamed *self;
    char *name;
{
    PyObject *rv;

    rv = PyMember_Get((char *)/*XXXX*/0, kstatnamed_memberlist, name);
    if (rv)
	    return rv;
    PyErr_Clear();
    return Py_FindMethod(kstatnamed_methods, (PyObject *)self, name);
}

static int
kstatnamed_setattr(self, name, v)
    kstatnamed *self;
    char *name;
    PyObject *v;
{
    /* XXXX Add your own setattr code here */
    if ( v == NULL ) {
	PyErr_SetString(PyExc_AttributeError, "Cannot delete attribute");
	return -1;
    }
    return PyMember_Set((char *)/*XXXX*/0, kstatnamed_memberlist, name, v);
}


static char Kstatnamedtype__doc__[] = 
""
;

static PyTypeObject Kstatnamedtype = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,					/*ob_size*/
    "kstatisticsnameddata",		/*tp_name*/
    sizeof(kstatnamed),			/*tp_basicsize*/
    0,					/*tp_itemsize*/
    /* methods */
    (destructor)kstatnamed_dealloc,	/*tp_dealloc*/
    (printfunc)0,			/*tp_print*/
    (getattrfunc)kstatnamed_getattr,	/*tp_getattr*/
    (setattrfunc)kstatnamed_setattr,	/*tp_setattr*/
    (cmpfunc)0,				/*tp_compare*/
    (reprfunc)kstatnamed_str,		/*tp_repr*/
    0,					/*tp_as_number*/
    0,					/*tp_as_sequence*/
    0,					/*tp_as_mapping*/
    (hashfunc)0,			/*tp_hash*/
    (ternaryfunc)0,			/*tp_call*/
    (reprfunc)kstatnamed_str,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Kstatnamedtype__doc__ 		/* Documentation string */
};



/* ---------- */




/* ---------------------------------------------------------------- */

static kstatdataobject *
newkstatdataobject(kc, ksp)
    kstat_ctl_t *kc;
    kstat_t *ksp;
{
    kstatdataobject *self;
    
    self = PyObject_NEW(kstatdataobject, &Kstatdatatype);
    if (self == NULL)
	return NULL;

    self->kc = kc;
    self->ksp = ksp;

    return self;
}

static void
kstatdata_dealloc(self)
    kstatdataobject *self;
{
    /* XXXX Add your own cleanup code here */

    PyMem_DEL(self);
}

static PyObject *
kstatdata_str(self)
    kstatdataobject *self;
{
    PyObject *s;
    char str[256];

    snprintf( str, 256, "%s/%s/%s", self->ksp->ks_module, self->ksp->ks_name, self->ksp->ks_class );
    s = PyString_FromString(str);

    /*
    s = Py_BuildValue("(sss)", self->ksp->ks_module, self->ksp->ks_name, self->ksp->ks_class);
    */

    return s;
}


static char kstat_Read__doc__[] =
""
;

static PyObject *
kstat_Read(self, args)
    kstatdataobject *self;
    PyObject *args;
{
    int r;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    r = kstat_read(self->kc, self->ksp, NULL);
    if( r == -1 )
	 return NULL;

    return Py_None;
}

static char kstat_Data_lookup__doc__[] =
""
;

static PyObject *
kstat_Data_lookup(self, args)
    kstatdataobject *self;
    PyObject *args;
{
    kstat_named_t *kn;
    char *dname;
    PyObject *ret;

    if (!PyArg_ParseTuple(args, "s", &dname))
	return NULL;

    kn = kstat_data_lookup(self->ksp, dname);

    ret = (PyObject *)newkstatnamed(kn);

    return ret;
}


static struct PyMethodDef kstatdata_methods[] = {
    {"read",		(PyCFunction)kstat_Read,	METH_VARARGS,	kstat_Read__doc__},
    {"data_lookup",	(PyCFunction)kstat_Data_lookup,	METH_VARARGS,	kstat_Data_lookup__doc__},
    {NULL,		NULL}		/* sentinel */
};

static struct memberlist kstatdata_memberlist[] = {
    /* XXXX Add lines like { "foo", T_INT, OFF(foo), RO }  */

    {NULL}	/* Sentinel */
};


static PyObject *
kstatdata_getattr(self, name)
    kstatobject *self;
    char *name;
{
    PyObject *rv;

    rv = PyMember_Get((char *)/*XXXX*/0, kstatdata_memberlist, name);
    if (rv)
	    return rv;
    PyErr_Clear();
    return Py_FindMethod(kstatdata_methods, (PyObject *)self, name);
}

static int
kstatdata_setattr(self, name, v)
    kstatobject *self;
    char *name;
    PyObject *v;
{
    /* XXXX Add your own setattr code here */
    if ( v == NULL ) {
	PyErr_SetString(PyExc_AttributeError, "Cannot delete attribute");
	return -1;
    }
    return PyMember_Set((char *)/*XXXX*/0, kstatdata_memberlist, name, v);
}


static char Kstatdatatype__doc__[] = 
""
;

static PyTypeObject Kstatdatatype = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,					/*ob_size*/
    "kstatisticsdata",			/*tp_name*/
    sizeof(kstatdataobject),		/*tp_basicsize*/
    0,					/*tp_itemsize*/
    /* methods */
    (destructor)kstatdata_dealloc,	/*tp_dealloc*/
    (printfunc)0,			/*tp_print*/
    (getattrfunc)kstatdata_getattr,	/*tp_getattr*/
    (setattrfunc)kstatdata_setattr,	/*tp_setattr*/
    (cmpfunc)0,				/*tp_compare*/
    (reprfunc)kstatdata_str,		/*tp_repr*/
    0,					/*tp_as_number*/
    0,					/*tp_as_sequence*/
    0,					/*tp_as_mapping*/
    (hashfunc)0,			/*tp_hash*/
    (ternaryfunc)0,			/*tp_call*/
    (reprfunc)kstatdata_str,		/*tp_str*/

    /* Space for future expansion */
    0L,0L,0L,0L,
    Kstatdatatype__doc__ 		/* Documentation string */
};



/* ---------- */



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

static char kstat_Lookup__doc__[] =
""
;

static PyObject *
kstat_Lookup(self, args)
    kstatobject *self;
    PyObject *args;
{
    PyObject *ret;
    kstat_t *kp;

    char *ks_module;
    int ks_instance;
    char *ks_name;

    if (!PyArg_ParseTuple(args, "sis", &ks_module, &ks_instance, &ks_name))
	return NULL;

    kp = kstat_lookup(self->kc, ks_module, ks_instance, ks_name);

    ret = (PyObject *)newkstatdataobject(self->kc, kp);
    return ret;
}


static char kstat_Close__doc__[] =
""
;

static void
kstat_Close(self, args)
    kstatobject *self;
    PyObject *args;
{
    kstat_close(self->kc);
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
    {"lookup",	(PyCFunction)kstat_Lookup,	METH_VARARGS,	kstat_Lookup__doc__},
    {"close",	(PyCFunction)kstat_Close,	METH_VARARGS,	kstat_Close__doc__},
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
    char str[256];

    snprintf( str, 256, "%s/%s/%s", self->kp->ks_module, self->kp->ks_name, self->kp->ks_class );
    s = PyString_FromString(str);

    /*
    s = Py_BuildValue("(s)", "testing");
    */

    /*
    if( self->kp != NULL )
	if( self->kp->ks_module != NULL && self->kp->ks_name != NULL && self->kp->ks_class != NULL )
	    s = Py_BuildValue("(sss)", self->kp->ks_module, self->kp->ks_name, self->kp->ks_class);
	else
	    s = Py_None;
    else
	s = Py_None;
    */

    return s;
}


/* Code to access structure members by accessing attributes */

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

/*
	    case KSTAT_TYPE_RAW:
		if( strcmp( self->kp->ks_name, "sysinfo" ) == 0 )
		    return build_sysinfo_data(self->kp);
*/
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



/* ---------------------------------------------------------------- */


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

    /*kstat_close(kc);*/

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



