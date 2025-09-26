# High-Resolution Image Synthesis with Latent Diffusion Models

## Authors
- Robin Rombach
- Andreas Blattmann
- Dominik Lorenz
- Patrick Esser
- Björn Ommer

## Metadata
- **arXiv ID**: 2112.10752
- **Submitted**: 20 Dec 2021
- **Last Revised**: 13 Apr 2022
- **Conference**: CVPR 2022
- **Primary Subject**: Computer Vision and Pattern Recognition (cs.CV)
- **Source**: https://arxiv.org/abs/2112.10752
- **Code**: https://github.com/CompVis/latent-diffusion

## Abstract

By decomposing the image formation process into a sequential application of denoising autoencoders, diffusion models (DMs) achieve state-of-the-art synthesis results on image data and beyond.

## Key Innovations

- **Latent Diffusion Models (LDMs)**: Operates in the latent space of pretrained autoencoders rather than directly on pixel space
- **Computational Efficiency**: Significantly reduces computational requirements compared to pixel-based diffusion models
- **High-Resolution Synthesis**: Enables generation of high-quality, high-resolution images
- **Cross-Attention Mechanism**: Incorporates conditioning information through cross-attention layers

## Technical Approach

- **Two-Stage Process**: First trains an autoencoder to map images to latent space, then applies diffusion in this compressed representation
- **Perceptual Compression**: Uses pretrained autoencoders to find perceptually equivalent but computationally more efficient representations
- **Flexible Conditioning**: Supports various conditioning modalities including text, semantic maps, and other images
- **Progressive Denoising**: Learns to progressively denoise latent representations

## Performance Achievements

- **State-of-the-Art Results**: Achieved leading performance across multiple image synthesis benchmarks
- **Image Inpainting**: Excellent results in filling missing parts of images
- **Unconditional Generation**: High-quality synthesis without conditioning
- **Semantic Scene Synthesis**: Ability to generate images from semantic segmentation maps
- **Super-Resolution**: Effective upscaling of low-resolution images

## Significance

This work fundamentally changed the landscape of AI-generated imagery by:

- **Democratizing Image Generation**: Made high-quality image synthesis computationally accessible
- **Foundation for Stable Diffusion**: Served as the theoretical foundation for the popular Stable Diffusion models
- **Text-to-Image Revolution**: Enabled the explosion of text-to-image applications that followed
- **Open Source Impact**: The released code and models became widely adopted in both research and industry

The Latent Diffusion Model architecture became the foundation for many subsequent generative AI applications, including Stable Diffusion, DALL-E 2 improvements, and numerous other text-to-image and image-to-image systems.