from django.test import TestCase
from tools import libbase


class ToolsTests(TestCase):

    def test_base_class(self):
        """
        Test abstract base class
        """
        class MyClass(libbase.ToolBase):
            def run(self):
                pass

        self.assertTrue(issubclass(MyClass, libbase.ToolBase))
        self.assertTrue(isinstance(MyClass(), libbase.ToolBase))

    def test_incomplete_base_class(self):
        """
        Check that base class fails to instantiate if it doesn't
        overload the run method
        """
        class MyClass(libbase.ToolBase):
            def norun(self):
                pass

        self.assertTrue(issubclass(MyClass, libbase.ToolBase))
        with self.assertRaises(TypeError):
            MyClass()