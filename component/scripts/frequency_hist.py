import ee
from natsort import natsorted

from component.message import cm

ee.Initialize()


def subset_items(list_: list):
    """from a list return first, middle and last element"""

    if len(list_) < 3:
        return list(set([list_[0]] + [list_[-1]]))
    else:
        return list((set([list_[0]] + [list_[int(len(list_) / 2)]] + [list_[-1]])))


def get_image_collection_ids(image_collection):
    """returns image collection ids"""
    return ee.ImageCollection(image_collection).aggregate_array("system:id").getInfo()


def get_unique_classes(aoi: ee.FeatureCollection, image_collection: ee.ImageCollection):
    """perfroms multiple (3) reductions over the image collection to luckly get all the
    classes. When no. images in image_collection <3, we extract all the classes in each
    image. If > 3 we expect that first, middle and last image contains all the classes
    in the image collection."""

    if not aoi:
        raise ValueError(cm.error.no_aoi)

    def get_classes(image, aoi):
        """perform individual image frequency histogram reduction"""

        # reduce the image
        image = ee.Image(image)
        band = image.bandNames().get(0)
        image = image.select([band])

        geometry = aoi.geometry()

        reduction = image.reduceRegion(
            ee.Reducer.frequencyHistogram(), geometry, maxPixels=1e13
        )

        # Remove all the unnecessary reducer output structure and make a
        # list of values.
        values = ee.Dictionary(reduction.get(image.bandNames().get(0))).keys().getInfo()

        return values

    image_ids = get_image_collection_ids(image_collection)
    subset_ids = subset_items(image_ids)

    # with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    #     futures = {
    #         executor.submit(get_classes, image_id, aoi): image_id
    #         for image_id in subset_ids
    #     }

    #     result = {}

    #     for future in concurrent.futures.as_completed(futures):
    #         future_name = futures[future]
    #         result[future_name] = future.result()

    result = {}

    for image_id in subset_ids:
        result[image_id] = get_classes(image_id, aoi)

    items = list(
        set([class_ for img_classes in result.values() for class_ in img_classes])
    )

    return {v: ("no_name", "#000000") for v in natsorted(items)}
