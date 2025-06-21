import stashapi.log as log
from stashapi.stashapp import StashInterface
import sys
import json


def processAll():
    pass


def processGallery(galleryId):
    gallery = stash.find_gallery(galleryId)
    if gallery is None:
        log.error(f"Gallery with id {galleryId} not found")
        return
    log.debug("galleryJson:")
    log.debug(gallery)

    if settings["demandOrganized"] and not gallery["organized"]:
            log.info(f"Excluding gallery {galleryId} because it is not organized")
            return
    galleryTagIds = [tag["id"] for tag in gallery["tags"]]
    if settings["excludeGalleryWithTag"] != "":
        galleryExclusionMarkerTag = stash.find_tag(settings["excludeGalleryWithTag"])
        if galleryExclusionMarkerTag is not None:
            if galleryExclusionMarkerTag["id"] in galleryTagIds:
                log.info(f"Excluding gallery {galleryId} because it has the tag {settings['excludeGalleryWithTag']}")
                return
    
    imageQuery = {
        "galleries": {
            "value": [galleryId],
            "modifier": "INCLUDES_ALL"
        }
    }
    if settings['excludeOrganized']:
        imageQuery["organized"] = False # type: ignore
    # if settings["excludeImageWithTag"] != "":
    #     imageExclusionMarkerTag = stash.find_tag(settings["excludeImageWithTag"])
    #     if imageExclusionMarkerTag is not None:
    #         imageQuery["tags"] = {
    #             "value": [imageExclusionMarkerTag["id"]],
    #             "modifier": "EXCLUDES"
    #         }
    #         galleryTagIds.append(imageExclusionMarkerTag["id"])

    galleryImageCount = stash.find_images(f=imageQuery, filter={"page": 0, "per_page": 0}, get_count=True)[0]

    if galleryImageCount > 0:
        galleryPerformerIds = [performer["id"] for performer in gallery["performers"]]

        log.info(f"Updating {galleryImageCount} images of gallery \"{gallery['title']}\" with tags {gallery['tags']}")

        galleryImagePageSize = 100
        galleryImagePage = 0
        while galleryImagePage * galleryImagePageSize < galleryImageCount:
            galleryImages = stash.find_images(f=imageQuery, filter={"page": galleryImagePage, "per_page": galleryImagePageSize}, fragment='id')
            galleryImageIds = [gallery_image['id'] for gallery_image in galleryImages]
            stash.update_images(
                {
                    "ids": galleryImageIds,
                    "performer_ids": {"mode": "ADD", "ids": galleryPerformerIds},
                    "tag_ids": {"mode": "ADD", "ids": galleryTagIds}
                }
            )
            log.debug(f"Updated {len(galleryImageIds)} images of gallery {galleryId}")
            galleryImagePage += 1
    

def processImage(id):
    return


json_input = json.loads(sys.stdin.read())
FRAGMENT_SERVER = json_input["server_connection"]
stash = StashInterface(FRAGMENT_SERVER)
config = stash.get_configuration()
settings = {
    "excludeOrganized": False,
    "demandOrganized": True,
    "excludeImageWithTag": "",
    "excludeGalleryWithTag": "",
}
if "syncGalleryAndImageTags" in config["plugins"]:
    settings.update(config["plugins"]["syncGalleryAndImageTags"])
if "mode" in json_input["args"]:
    PLUGIN_ARGS = json_input["args"]["mode"]
    if "processAll" in PLUGIN_ARGS:
        log.info("Processing all galleries and images")
        processAll()
elif "hookContext" in json_input["args"]:
    id = json_input["args"]["hookContext"]["id"]
    log.debug("hookContextJson:")
    log.debug(json_input["args"]["hookContext"])
    if json_input["args"]["hookContext"]["type"] in {"Gallery.Update.Post", "Gallery.Create.Post"}:
        log.info(f"Processing gallery {id}")
        processGallery(id)
    elif json_input["args"]["hookContext"]["type"] in {"Image.Update.Post" or "Image.Create.Post"}:
        log.info(f"Processing image {id}")
        processImage(id)
