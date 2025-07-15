from django.test import TestCase

from ness_comms.models import UserInput

# Create your tests here.

class OutputEventDataUploadTestCase(TestCase):
    def setUp(self):
        UserInput.objects.create(raw_data="870003610001002301261821543d")
        UserInput.objects.create(raw_data="8700836125580323012618222869")

    def test_data_checksum(self):
        """Check if checksum is calculated correctly"""
        data_1 = UserInput.objects.get(raw_data="870003610001002301261821543d")
        data_2 = UserInput.objects.get(raw_data="8700836125580323012618222869")
        self.assertEqual(data_1.generateChecksum(), "3d", msg="Checksum does not match!")
        self.assertEqual(data_2.generateChecksum(), "69", msg="Checksum does not match!")