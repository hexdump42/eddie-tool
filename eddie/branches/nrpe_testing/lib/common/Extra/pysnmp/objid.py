"""
   Convert ASN.1 Object ID between various representations.

   Written by Ilya Etingof <ilya@glas.net>, 06/2000

"""
import string
import error

class objid:
    """Implement various convertions of ASN1 Object ID's value
    """
    def str2nums (self, txt):
        """
           str2nums(obj_id) -> object id
           
           Convert Object ID (given as string) into a list of integer
           sub IDs.
        """
        if not txt:
            raise error.BadArgument('Empty Object ID')

        # Convert string into a list and filter out empty members
        # (leading dot causes this)
        objid_s = string.split(txt, '.')
        objid_s = filter(lambda x: len(x), objid_s)

        # Convert a list of symbols into a list of numbers
        try:
            objid_n = map(lambda x: string.atol(x), objid_s)

        except:
            raise error.BadArgument('Malformed Object ID: ' + str(txt))

        if not len(objid_n):
            raise error.BadArgument('Empty Object ID: ' + str(txt))

        return objid_n

    def nums2str (self, objid_n):
        """
           nums2str(obj_id) -> object id
           
           Convert Object ID (given as a list of integer sub Object IDs) into
           string representation.
        """
        if not objid_n:
            raise error.BadArgument('Empty numeric Object ID')

        # Convert a list of number into a list of symbols
        try:
            objid_s = map(lambda x: '.%lu' % x, objid_n)

        except:
            raise error.BadArgument('Malformed numeric Object ID: ' + str(objid_n))
 
        # Merge all the list members into a string
        txt = reduce(lambda x, y: x+y, objid_s)
        if not len(txt):
            raise error.BadArgument('Empty numeric Object ID: ' + str(objid_n))

        return txt

