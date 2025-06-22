import stashapi.log as log
from stashapi.stashapp import StashInterface
import sys
import json

def processAll():
    pass

def processImage(imageId):
    image = stash.find_image(imageId)
    if image is None:
        log.error(f"Image with id {imageId} not found")
        return
    log.debug("imageJson:")
    log.debug(image)

    if settings["demandOrganized"] and not image["organized"]:
        log.info(f"Excluding image {imageId} because it is not organized")
        return
    
    imageTagIds = [tag["id"] for tag in image["tags"]]
    if settings["excludeImageWithTag"] != "":
        imageExclusionMarkerTag = stash.find_tag(settings["excludeImageWithTag"])
        if imageExclusionMarkerTag is not None:
            if imageExclusionMarkerTag["id"] in imageTagIds:
                log.info(f"Excluding image {imageId} because it has the tag {settings['excludeImageWithTag']}")
                return
    if settings["excludeGalleryWithTag"] != "":
        galleryExclusionMarkerTag = stash.find_tag(settings["excludeGalleryWithTag"])
        if galleryExclusionMarkerTag is not None:
            imageTagIds.append(galleryExclusionMarkerTag["id"])

    performerIds = [performer["id"] for performer in image["performers"]]

    galleryIds = []
    for gallery in image["galleries"]:
        if settings['excludeOrganized'] and not gallery["organized"]:
            log.info(f"Excluding gallery {gallery['id']} because it is not organized")
        else:
            galleryIds.append(gallery["id"])
    if len(galleryIds) == 0:
        log.info(f"Excluding image {imageId} because it has no galleries")
        return
    log.info(f"Updating {len(galleryIds)} galleries of image \"{image['title']}\" with tags {image['tags']}")
    stash.update_galleries(
        {
            "ids": galleryIds,
            "performer_ids": {"mode": "ADD", "ids": performerIds},
            "tag_ids": {"mode": "ADD", "ids": imageTagIds}
        }
    )   
    


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
if "tagGalleriesWithImageTags" in config["plugins"]:
    settings.update(config["plugins"]["tagGalleriesWithImageTags"].get("settings", {}))
if "hookContext" in json_input["args"]:
    id = json_input["args"]["hookContext"]["id"]
    if json_input["args"]["hookContext"]["type"] in {"Image.Update.Post", "Image.Create.Post"}:
        log.info(f"Processing Image {id}")
        processImage(id)
