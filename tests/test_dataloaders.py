import pytest
import sys, os
import torchvision
sys.path.insert(0,"../torchxrayvision/")
import torchxrayvision as xrv
import shutil

file_path = os.path.abspath(os.path.dirname(__file__))
 
dataset_classes = [xrv.datasets.NIH_Dataset,
                   xrv.datasets.PC_Dataset,
                   xrv.datasets.NIH_Google_Dataset,
                   xrv.datasets.Openi_Dataset,
                   xrv.datasets.CheX_Dataset,
                   xrv.datasets.SIIM_Pneumothorax_Dataset,
                   xrv.datasets.VinBrain_Dataset]

test_data_path = "/tmp/testdata"
test_png_img_file = os.path.join(file_path,"00000001_000.png")
test_jpg_img_file = os.path.join(file_path,"16747_3_1.jpg")
test_dcm_img_file = os.path.join(file_path,"1.2.276.0.7230010.3.1.4.8323329.6904.1517875201.850819.dcm")

def get_clazz_imgpath(clazz):
    return os.path.join(test_data_path, clazz.__name__)

def create_test_img(test_img_file, clazz, filename):
    imgpath = get_clazz_imgpath(clazz)
    os.makedirs(os.path.join(imgpath, os.path.dirname(filename)))
    shutil.copyfile(test_img_file, os.path.join(imgpath, filename))
    

@pytest.fixture(scope="session", autouse=True)
def create_test_images(request):
    
    if os.path.exists(test_data_path):
        shutil.rmtree(test_data_path)
    
    # for nih dataset
    create_test_img(test_png_img_file, xrv.datasets.NIH_Dataset, "00000001_000.png")
    create_test_img(test_png_img_file, xrv.datasets.PC_Dataset, "125374151943505747025890313053997514922_j5rk5q.png")
    create_test_img(test_png_img_file, xrv.datasets.NIH_Google_Dataset, "00000211_006.png")
    create_test_img(test_png_img_file, xrv.datasets.Openi_Dataset, "CXR10_IM-0002-1001.png")
    create_test_img(test_jpg_img_file, xrv.datasets.CheX_Dataset, "train/patient00004/study1/view1_frontal.jpg")
    create_test_img(test_dcm_img_file, xrv.datasets.SIIM_Pneumothorax_Dataset, "1.2.276.0.7230010.3.1.2.8323329.6904.1517875201.850818/1.2.276.0.7230010.3.1.3.8323329.6904.1517875201.850817/1.2.276.0.7230010.3.1.4.8323329.6904.1517875201.850819.dcm")
    create_test_img(test_dcm_img_file, xrv.datasets.VinBrain_Dataset, "000434271f63a053c4128a0ba6352c7f.dicom")
    
    


def test_dataloader_basic(create_test_images):
    
    transform = torchvision.transforms.Compose([xrv.datasets.XRayCenterCrop(),
                                                xrv.datasets.XRayResizer(224)])
    
    for dataset_class in dataset_classes:
        dataset = dataset_class(imgpath=get_clazz_imgpath(dataset_class), transform=transform)
        
        sample = dataset[0]
        
        assert("img" in sample)
        assert("lab" in sample)
        assert("idx" in sample)
        

def test_dataloader_merging():
    
    datasets = []
    for dataset_class in dataset_classes:
        dataset = dataset_class(imgpath=".")
        datasets.append(dataset)
    
    for dataset in datasets:
        xrv.datasets.relabel_dataset(xrv.datasets.default_pathologies, dataset)
        
    dd = xrv.datasets.MergeDataset(datasets)
    
    # also test alias
    dd = xrv.datasets.Merge_Dataset(datasets)
    
def test_dataloader_merging_dups():
    
    datasets = []
    for dataset_class in dataset_classes:
        dataset = dataset_class(imgpath=".")
        datasets.append(dataset)
    
    for dataset in datasets:
        xrv.datasets.relabel_dataset(xrv.datasets.default_pathologies, dataset)
    
    for dataset in datasets:
        dd = xrv.datasets.Merge_Dataset([dataset,dataset])
        
    #now merge merge datasets
    for dataset in datasets:
        dd = xrv.datasets.Merge_Dataset([dataset,dataset])
        dd = xrv.datasets.Merge_Dataset([dd,dd])

# test that we catch incorrect pathology alignment
def test_dataloader_merging_incorrect_alignment():
    with pytest.raises(Exception) as excinfo:
    
        d_nih = xrv.datasets.NIH_Dataset(imgpath=".")
        d_pc = xrv.datasets.PC_Dataset(imgpath=".")

        dd = xrv.datasets.Merge_Dataset([d_nih, d_pc])
        
    assert "incorrect pathology alignment" in str(excinfo.value)
    
    
    with pytest.raises(Exception) as excinfo:
    
        d_nih = xrv.datasets.NIH_Dataset(imgpath=".")
        d_pc = xrv.datasets.PC_Dataset(imgpath=".")
        xrv.datasets.relabel_dataset(xrv.datasets.default_pathologies, d_nih)
        xrv.datasets.relabel_dataset(xrv.datasets.default_pathologies[:-1], d_pc)

        dd = xrv.datasets.Merge_Dataset([d_nih, d_pc])
        
    assert "incorrect pathology alignment" in str(excinfo.value)
    
