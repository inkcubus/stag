import os
from bs4 import BeautifulSoup

class XMPHandler:

    @staticmethod
    def is_xmp_file(filename):
        filename, file_extension = os.path.splitext(filename)
        return file_extension.lower() == ".xmp"

    @staticmethod
    def possible_names_for_image(filename):
        base, _ = os.path.splitext(filename)
        return [
            filename + "." + "xmp",
            base + "." + "xmp"
        ]

    @staticmethod
    def get_xmp_sidecars_for_image(filename):
        file_list = []
        for current in XMPHandler.possible_names_for_image(filename):
            if os.path.exists(current):
                file_list.append(current)
        return file_list

    @staticmethod
    def get_xmp_sidecar(filename, prefer_short = False):
        possible_names = XMPHandler.possible_names_for_image(filename)

        if prefer_short:
            possible_names.reverse()
        
        for current in possible_names:
            if os.path.exists(current):
                return current

    @staticmethod
    def create_xmp_sidecar(image_filename, prefer_exact_filenames):
        filename, file_extension = os.path.splitext(image_filename)
        xmp_name = None
        if prefer_exact_filenames:
            xmp_name = image_filename + ".xmp"
        else:
            xmp_name = filename + ".xmp"
        basename = os.path.basename(image_filename)
        soup = BeautifulSoup("""
                <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">
                 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
                  <rdf:Description rdf:about=""
                    xmlns:exif="http://ns.adobe.com/exif/1.0/"
                    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
                    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/">
                  </rdf:Description>
                 </rdf:RDF>
                </x:xmpmeta>
                """, "xml")
        desc = soup("rdf:Description")[0]
        desc["xmpMM:DerivedFrom"] = basename
        print ("creating xmp sidecar file at ",xmp_name)
        with open(xmp_name, 'w') as f:
            f.write(str(soup))
        return xmp_name


    def __init__(self, xmp_file_path):

        self.path = xmp_file_path

        with open(xmp_file_path, 'r') as f:
            data = f.read()
            self.soup = BeautifulSoup(data, "xml")

        self.ensure_namespace("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        self.subject = self.ensure_keyword_bag("dc:subject")

        self.ensure_namespace("xmlns:lr", "http://ns.adobe.com/lightroom/1.0/")
        self.hierarchical_subject = self.ensure_keyword_bag("lr:hierarchicalSubject")

    def has_subject_prefix(self, prefix):
        subjects = None
        if self.subject("rdf:Bag"):                      # unfortunately, we have to account for the piece of
            subjects = self.subject("rdf:Bag")[0]        # useless junk that ON1 photo raw is, because it uses
        elif self.subject("rdf:Seq"):                    # seq instead of bag like everyone else....
            subjects = self.subject("rdf:Seq")[0]
        if subjects is None:
            return False
        for i in subjects("rdf:li"):
            if i.string.lower() == prefix.lower():
                return True
        return False

    def ensure_keyword_bag(self, kw_tag):
        desc = self.soup("rdf:Description")[0]
        if len(self.soup(kw_tag)) == 0:
            subj = self.soup.new_tag(kw_tag)
            bag = self.soup.new_tag("rdf:Bag")
            subj.append(bag)
            desc.append(subj)
        return self.soup(kw_tag)[0]

    def ensure_namespace(self, namespace, url):
        desc = self.soup("rdf:Description")[0]
        try:
            _ = desc[namespace]
        except KeyError:
            desc[namespace] = url

    def save(self):
        print ("writing to ",self.path)
        if len(str(self.soup))==0:
            print ("ERROR: soup creation failed. not writing XMP file")
            return
        with open(self.path, 'w') as f:
            f.write(str(self.soup))
            
    def add_single_subject(self, new_subject):
        subjects = None
        if self.subject("rdf:Bag"):                      
            subjects = self.subject("rdf:Bag")[0]       # see above  
        elif self.subject("rdf:Seq"):                    
            subjects = self.subject("rdf:Seq")[0]
        for i in subjects("rdf:li"):
            if i.string == new_subject:
                return
        newTag = self.soup.new_tag("rdf:li")
        newTag.string = new_subject
        subjects.append (newTag)
        
    def add_hierarchical_subject(self, hs):
        subjects = None
        if self.hierarchical_subject("rdf:Bag"):
            subjects = self.hierarchical_subject("rdf:Bag")[0]
        elif self.hierarchical_subject("rdf:Seq"):
            subjects = self.hierarchical_subject("rdf:Seq")[0]
        for i in subjects:
            if i.string == hs:
                return
        new_tag = self.soup.new_tag("rdf:li")
        new_tag.string = hs
        subjects.append (new_tag)
        subjects = hs.split("|")
        for s in subjects:
            self.add_single_subject(s)

    def strip_date_time_original(self):
        desc = self.soup("rdf:Description")[0]
        try:
            del desc["exif:DateTimeOriginal"]
        except KeyError:
            pass

    def set_output_path(self, new_path):
        self.path = new_path

if __name__ == '__main__':
    print (XMPHandler.get_xmp_sidecars_for_image("test/P1012424.ORF"))