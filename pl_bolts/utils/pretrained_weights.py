

urls = {
    'vae-imagenet': 'https://pl-bolts-weights.s3.us-east-2.amazonaws.com/vae/version_0/checkpoints/epoch%3D2.ckpt',
    'CPCV2-resnet18': 'https://pl-bolts-weights.s3.us-east-2.amazonaws.com/cpc/resnet18_version_6/checkpoints/epoch%3D85.ckpt'
}


def load_pretrained(model, class_name=None):
    if class_name is None:
        class_name = model.__class__.__name__
    ckpt_url = urls[class_name]
    weights_model = model.__class__.load_from_checkpoint(ckpt_url)
    model.load_state_dict(weights_model.state_dict())